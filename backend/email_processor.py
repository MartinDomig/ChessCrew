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

from config import DOMAIN, ADMIN_EMAIL, SMTP_SERVER, SMTP_PORT, TRUSTED_MAIL_SERVER

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

def get_player_emails(player):
    """Get all email addresses for a player, handling multiple emails separated by various delimiters"""
    if not player.email or not player.email.strip():
        return []
    
    # Split by common delimiters: comma, semicolon, space
    import re
    emails = re.split(r'[,;\s]+', player.email.strip())
    
    # Clean up and validate emails
    valid_emails = []
    for email in emails:
        email = email.strip()
        if email and '@' in email:  # Basic email validation
            valid_emails.append(email)
    
    return valid_emails

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
        # Case insensitive replacement - find all variations of the placeholder
        import re
        pattern = re.escape(placeholder).replace(r'\{', r'\{').replace(r'\}', r'\}')
        personalized = re.sub(pattern, value, personalized, flags=re.IGNORECASE)

    return personalized

def remove_tag_from_subject(subject):
    """Remove [tag:xxx] from subject line"""
    if not subject:
        return subject
    return re.sub(r'\[tag:[^\]]+\]\s*', '', subject, flags=re.IGNORECASE)

def send_personalized_email(original_msg, player, smtp_server=SMTP_SERVER, smtp_port=SMTP_PORT):
    """Send a personalized email to a specific player"""

    # Determine if we need multipart based on content and attachments
    has_attachments = False
    if original_msg.is_multipart():
        for part in original_msg.walk():
            if (part.get_content_maintype() != 'multipart' and 
                part.get('Content-Disposition') is not None and 
                part.get_filename()):
                has_attachments = True
                break

    # Create appropriate message structure
    if has_attachments:
        # Use mixed multipart for attachments
        msg = MIMEMultipart('mixed')
    else:
        # Use alternative for text/html alternatives
        msg = MIMEMultipart('alternative')
    
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

    # Create text content container
    if has_attachments and (plain_text_body and html_body):
        # If we have attachments AND both text formats, create an alternative container for text
        text_container = MIMEMultipart('alternative')
        personalized_plain = personalize_content(plain_text_body, player)
        text_container.attach(MIMEText(personalized_plain, 'plain', 'utf-8'))
        personalized_html = personalize_content(html_body, player)
        text_container.attach(MIMEText(personalized_html, 'html', 'utf-8'))
        msg.attach(text_container)
    else:
        # Add text content directly (for no attachments OR single text format)
        if plain_text_body:
            personalized_plain = personalize_content(plain_text_body, player)
            msg.attach(MIMEText(personalized_plain, 'plain', 'utf-8'))

        if html_body:
            personalized_html = personalize_content(html_body, player)
            msg.attach(MIMEText(personalized_html, 'html', 'utf-8'))

    # Copy attachments from original message (only once)
    if has_attachments and original_msg.is_multipart():
        for part in original_msg.walk():
            # Skip multipart containers
            if part.get_content_maintype() == 'multipart':
                continue
            # Skip text/html content parts (not attachments)
            if part.get_content_type() in ['text/plain', 'text/html']:
                continue
            # Only process actual attachments
            if part.get('Content-Disposition') is not None and part.get_filename():
                filename = part.get_filename()
                attachment = MIMEBase(part.get_content_maintype(), part.get_content_subtype())
                attachment.set_payload(part.get_payload(decode=True))
                encoders.encode_base64(attachment)
                attachment.add_header('Content-Disposition', f'attachment; filename="{filename}"')
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

def is_authenticated_sender(msg):
    """Check if email was sent by authenticated SMTP user via our server"""
    # Check for SMTP authentication in Received headers from our server
    received_headers = msg.get_all('Received', [])
    for received in received_headers:
        # Look for ESMTPSA from our specific mail server
        if ('esmtpsa' in received.lower() and 
            TRUSTED_MAIL_SERVER.lower() in received.lower()):
            return True
        # Also check for other authentication indicators from our server
        if (TRUSTED_MAIL_SERVER.lower() in received.lower() and 
            any(auth_indicator in received.lower() for auth_indicator in [
                'sasl_authenticated', 'authenticated', 'auth=pass'
            ])):
            return True
    
    return False

def send_summary_email(original_msg, summary_content):
    """Send a summary email back to the admin with processing results"""
    try:
        # Create multipart message to include both summary and original email
        summary_msg = MIMEMultipart()
        summary_msg['From'] = f"ChessCrew Email Processor <{ADMIN_EMAIL}>"
        summary_msg['To'] = ADMIN_EMAIL
        summary_msg['Subject'] = f"Re: {remove_tag_from_subject(original_msg['Subject'] or 'No Subject')}"
        
        # Add reply headers to make email clients recognize this as a reply
        message_id = original_msg.get('Message-ID')
        if message_id:
            summary_msg['In-Reply-To'] = message_id
            summary_msg['References'] = message_id
        
        # Add the summary as the main body
        summary_part = MIMEText(summary_content, 'plain', 'utf-8')
        summary_msg.attach(summary_part)
        
        # Add the original email as an attachment
        original_attachment = MIMEText(original_msg.as_string(), 'plain', 'utf-8')
        original_attachment.add_header('Content-Disposition', 'attachment', filename='original_email.txt')
        summary_msg.attach(original_attachment)
        
        # Copy any attachments from the original email
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
                    attachment.add_header('Content-Disposition', f'attachment; filename="original_{filename}"')
                    summary_msg.attach(attachment)
        
        # Send the summary
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.sendmail(ADMIN_EMAIL, ADMIN_EMAIL, summary_msg.as_string())
        server.quit()
        return True
    except Exception as e:
        print(f"Failed to send summary email: {e}", file=sys.stderr)
        return False

def main():
    summary_lines = []  # Collect all log output for summary
    
    try:
        # Parse the incoming email
        msg = parse_email_from_stdin()

        # Security checks: verify sender is authenticated and from admin
        from_addr = email.utils.parseaddr(msg['From'])[1]
        if from_addr != ADMIN_EMAIL:
            error_msg = f"Email from {from_addr} is not from admin, disregarding."
            print(error_msg, file=sys.stderr)
            summary_lines.append(f"❌ REJECTED: {error_msg}")
            send_summary_email(msg, "\n".join(summary_lines))
            return
            
        if not is_authenticated_sender(msg):
            error_msg = f"Email from {from_addr} was not sent via authenticated SMTP, disregarding for security."
            print(error_msg, file=sys.stderr)
            summary_lines.append(f"❌ REJECTED: {error_msg}")
            send_summary_email(msg, "\n".join(summary_lines))
            return

        summary_lines.append(f"✅ ACCEPTED: Email from {from_addr} passed security checks")

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
            error_msg = "No tag found in subject line. Expected format: [tag:tagname]"
            print(error_msg, file=sys.stderr)
            summary_lines.append(f"❌ ERROR: {error_msg}")
            send_summary_email(msg, "\n".join(summary_lines))
            return

        summary_lines.append(f"📧 PROCESSING: Tag '{tag}' found in subject")

        # Process the tag
        emails_sent = 0
        failed_emails = []

        # Get players with this tag
        players = get_players_by_tag(tag)

        if not players:
            error_msg = f"No players found with tag '{tag}'"
            print(error_msg, file=sys.stderr)
            summary_lines.append(f"❌ ERROR: {error_msg}")
            send_summary_email(msg, "\n".join(summary_lines))
            return

        log_msg = f"Sending email to {len(players)} players with tag '{tag}'"
        print(log_msg, file=sys.stderr)
        summary_lines.append(f"📬 SENDING: {log_msg}")

        # Send personalized email to each player
        for player in players:
            player_emails = get_player_emails(player)
            if not player_emails:
                summary_lines.append(f"  ❌ {player.name} - No valid email addresses")
                continue
                
            # Send to each email address for this player
            for email_addr in player_emails:
                # Create a temporary player object with single email for sending
                temp_player = type('Player', (), {})()
                for attr in ['first_name', 'last_name', 'name', 'female', 'club', 'elo', 'fide_elo', 'p_number', 'fide_number']:
                    setattr(temp_player, attr, getattr(player, attr, None))
                temp_player.email = email_addr
                
                if send_personalized_email(msg, temp_player):
                    emails_sent += 1
                    success_msg = f"Sent email to {email_addr}"
                    print(success_msg, file=sys.stderr)
                    if len(player_emails) > 1:
                        summary_lines.append(f"  ✅ {player.name} ({email_addr})")
                    else:
                        summary_lines.append(f"  ✅ {player.name} ({email_addr})")
                else:
                    fail_msg = f"Failed to send email to {email_addr}"
                    print(fail_msg, file=sys.stderr)
                    failed_emails.append(email_addr)
                    summary_lines.append(f"  ❌ {player.name} ({email_addr}) - FAILED")

        final_msg = f"Total emails sent: {emails_sent}"
        print(final_msg, file=sys.stderr)
        summary_lines.append(f"\n📊 SUMMARY:")
        summary_lines.append(f"  • Successfully sent: {emails_sent}")
        summary_lines.append(f"  • Failed: {len(failed_emails)}")
        summary_lines.append(f"  • Total players with tag '{tag}': {len(players)}")
        
        if failed_emails:
            summary_lines.append(f"\n❌ FAILED EMAILS:")
            for email_addr in failed_emails:
                summary_lines.append(f"  • {email_addr}")

        # Send summary email back to admin
        send_summary_email(msg, "\n".join(summary_lines))

    except Exception as e:
        error_msg = f"Error processing email: {e}"
        print(error_msg, file=sys.stderr)
        summary_lines.append(f"💥 FATAL ERROR: {error_msg}")
        try:
            send_summary_email(msg, "\n".join(summary_lines))
        except:
            pass  # If we can't send summary, at least don't crash
        sys.exit(1)

if __name__ == '__main__':
    main()