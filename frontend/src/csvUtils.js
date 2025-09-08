export function exportEmailList(players) {
  if (!players || players.length === 0) {
    alert('Keine Spieler zum Exportieren gefunden.');
    return;
  }
  const header = ['First Name', 'Last Name', 'Email', 'Gender'];
  const rows = [];
  const emailRegex = /[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}/;
  players.forEach(p => {
    const gender = p.female ? 'female' : 'male';
    const emails = (p.email || '').split(/[,;\s]+/).filter(e => emailRegex.test(e));
    emails.forEach(email => {
      if (email) {
        rows.push([p.first_name, p.last_name, email, gender]);
      }
    });
  });
  if (rows.length === 0) {
    alert('Keine gültigen E-Mail-Adressen in der aktuellen Auswahl gefunden.');
    return;
  }
  
  // Show confirmation with count
  const playerCount = players.length;
  const emailCount = rows.length;
  const confirmed = confirm(`${emailCount} E-Mail-Adresse${emailCount !== 1 ? 'n' : ''} von ${playerCount} Spieler${playerCount !== 1 ? 'n' : ''} exportieren?`);
  if (!confirmed) return;
  
  const csvContent = [header, ...rows]
    .map(row => row.map(field => {
      // Only quote if field contains comma, quote, or newline
      return /[",\n]/.test(field) ? `"${field.replace(/"/g, '""')}` : field;
    }).join(','))
    .join('\n');
  const blob = new Blob([csvContent], { type: 'text/csv' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = 'players.csv';
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}
