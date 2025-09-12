#!/usr/bin/env python3
"""
ChessCrew Email Processor

This script processes incoming emails sent to chesscrew.[tag]@domig.net addresses.
It extracts the tag from the recipient address, finds all players with that tag,
and sends personalized emails to each recipient.

Usage: This script is called by postfix as a mail filter.
"""

import sys
import os
import email
import email.utils
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import tempfile
import magic
import re
from pathlib import Path

from config import DOMAIN, ADMIN_EMAIL, SMTP_SERVER, SMTP_PORT

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from db.models import db, Player, Tag
from flask import Flask

def create_app():
    """Create Flask app for database access"""
    app = Flask(__name__)

    # Database configuration
    db_dir = backend_dir / 'db'
    db_path = db_dir / 'chesscrew.sqlite3'
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)
    return app

def get_players_by_tag(tag_name):
    """Get all players with a specific tag who have email addresses"""
    with create_app().app_context():
        tag = Tag.query.filter_by(name=tag_name).first()
        if not tag:
            return []

        players = []
        for player in tag.players:
            if player.email and player.email.strip():
                players.append(player)

        return players

def parse_email_from_stdin():
    """Parse email from stdin (postfix pipe format)"""
    raw_email = sys.stdin.read()
    return email.message_from_string(raw_email)

def get_tag_from_recipient(recipient):
    """Extract tag from recipient address like chesscrew.tag@domig.net"""
    match = re.match(fr'chesscrew\.([^@]+)@{DOMAIN}', recipient, re.IGNORECASE)
    if match:
        return match.group(1)
    return None

def get_tag_from_subject(subject):
    """Extract tag from subject line like [tag:youth] Tournament info"""
    if not subject:
        return None
    match = re.search(r'\[tag:([^\]]+)\]', subject, re.IGNORECASE)
    if match:
        return match.group(1)
    return None

def get_gender_greeting(female):
    """Get gender-specific greeting"""
    return "Liebe" if female else "Lieber"

def personalize_content(content, player):
    """Replace placeholders in email content with player-specific data"""
    replacements = {
        '{vorname}': player.first_name,
        '{nachname}': player.last_name,
        '{name}': player.name,
        '{greeting}': get_gender_greeting(player.female),
        '{email}': player.email,
        '{verein}': player.club or '',
        '{elo}': str(player.elo) if player.elo else '',
        '{fide_elo}': str(player.fide_elo) if player.fide_elo else '',
        '{spielernummer}': str(player.p_number) if player.p_number else '',
        '{fidenummer}': str(player.fide_number) if player.fide_number else '',
    }

    personalized = content
    for placeholder, value in replacements.items():
        personalized = personalized.replace(placeholder, value)

    return personalized

def remove_tag_from_subject(subject):
    """Remove [tag:xxx] from subject line"""
    if not subject:
        return subject
    return re.sub(r'\[tag:[^\]]+\]\s*', '', subject, flags=re.IGNORECASE)

def send_personalized_email(original_msg, player, smtp_server=SMTP_SERVER, smtp_port=SMTP_PORT):
    """Send a personalized email to a specific player"""

    # Create new message
    msg = MIMEMultipart('alternative')  # Use 'alternative' for plain/HTML versions
    msg['From'] = original_msg['From']
    msg['To'] = player.email
    
    # Remove tag from subject before personalizing
    clean_subject = remove_tag_from_subject(original_msg['Subject'] or '')
    msg['Subject'] = personalize_content(clean_subject, player)

    # Process the original message content
    plain_text_body = None
    html_body = None

    if original_msg.is_multipart():
        # Extract both plain text and HTML parts
        for part in original_msg.walk():
            if part.get_content_type() == 'text/plain':
                try:
                    plain_text_body = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                except:
                    plain_text_body = part.get_payload(decode=True).decode('latin-1', errors='ignore')
            elif part.get_content_type() == 'text/html':
                try:
                    html_body = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                except:
                    html_body = part.get_payload(decode=True).decode('latin-1', errors='ignore')
    else:
        # Single part message
        content_type = original_msg.get_content_type()
        try:
            body = original_msg.get_payload(decode=True).decode('utf-8', errors='ignore')
        except:
            body = original_msg.get_payload(decode=True).decode('latin-1', errors='ignore')

        if content_type == 'text/html':
            html_body = body
        else:
            plain_text_body = body

    # Personalize content
    if plain_text_body:
        personalized_plain = personalize_content(plain_text_body, player)
        msg.attach(MIMEText(personalized_plain, 'plain', 'utf-8'))

    if html_body:
        personalized_html = personalize_content(html_body, player)
        msg.attach(MIMEText(personalized_html, 'html', 'utf-8'))

    # Copy attachments from original message
    if original_msg.is_multipart():
        for part in original_msg.walk():
            if part.get_content_maintype() == 'multipart':
                continue
            if part.get('Content-Disposition') is None:
                continue

            filename = part.get_filename()
            if filename:
                attachment = MIMEBase(part.get_content_maintype(), part.get_content_subtype())
                attachment.set_payload(part.get_payload(decode=True))
                encoders.encode_base64(attachment)
                attachment.add_header('Content-Disposition', f'attachment; filename="{filename}"')
                # Add attachment to the main message (not the alternative part)
                if msg.get_payload():
                    msg.get_payload().append(attachment)
                else:
                    msg.attach(attachment)

    # Send the email
    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.sendmail(msg['From'], player.email, msg.as_string())
        server.quit()
        return True
    except Exception as e:
        print(f"Failed to send email to {player.email}: {e}", file=sys.stderr)
        return False

def main():
    try:
        # Parse the incoming email
        msg = parse_email_from_stdin()

        # if mail does not come from admin, disregard it
        from_addr = email.utils.parseaddr(msg['From'])[1]
        if from_addr != ADMIN_EMAIL:
            print(f"Email from {from_addr} is not from admin, disregarding.", file=sys.stderr)
            return

        # Get all recipients
        recipients = []
        if msg['To']:
            recipients.extend(email.utils.getaddresses([msg['To']]))
        if msg['Cc']:
            recipients.extend(email.utils.getaddresses([msg['Cc']]))
        if msg['Bcc']:
            recipients.extend(email.utils.getaddresses([msg['Bcc']]))

        # Extract tag from subject line
        tag = get_tag_from_subject(msg['Subject'])
        if not tag:
            print("No tag found in subject line. Expected format: [tag:tagname]", file=sys.stderr)
            return

        # Process the tag
        emails_sent = 0

        # Get players with this tag
        players = get_players_by_tag(tag)

        if not players:
            print(f"No players found with tag '{tag}'", file=sys.stderr)
            return

        print(f"Sending email to {len(players)} players with tag '{tag}'", file=sys.stderr)

        # Send personalized email to each player
        for player in players:
            if send_personalized_email(msg, player):
                emails_sent += 1
                print(f"Sent email to {player.email}", file=sys.stderr)
            else:
                print(f"Failed to send email to {player.email}", file=sys.stderr)

        print(f"Total emails sent: {emails_sent}", file=sys.stderr)

    except Exception as e:
        print(f"Error processing email: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()