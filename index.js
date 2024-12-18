import { google } from 'googleapis';
import { Octokit } from '@octokit/rest';


const octokit = new Octokit({ auth: process.env.GITHUB_TOKEN });
const credentials = JSON.parse(process.env.GOOGLE_CREDENTIALS);

const auth = new google.auth.GoogleAuth({
    credentials,
    scopes: ['https://www.googleapis.com/auth/spreadsheets']
});
const sheets = google.sheets({ version: 'v4', auth });

const spreadsheetId = '1YdCcHmGOKrHJed4brXRxZ2T4DiDjqDqqdRGoSWvhQ54'; // ID del file excel

const prNumber = process.env.GITHUB_REF.split('/')[2];
const repoOwner = process.env.GITHUB_REPOSITORY.split('/')[0];
const repoName = process.env.GITHUB_REPOSITORY.split('/')[1];

(async () => {
    const prResponse = await octokit.pulls.get({
    owner: repoOwner,
    repo: repoName,
    pull_number: prNumber
    });

    const prBody = prResponse.data.body;

    const timeSpentMatch = prBody.match(/tempo impiegato:\s*(\d+)/i);
    if (!timeSpentMatch) {
    throw new Error('Tempo impiegato non trovato nella descrizione della pull request.');
    }
    const timeSpent = parseInt(timeSpentMatch[1], 10);

    const issueMatch = prBody.match(/closes\s+#(\d+)/i);
    if (!issueMatch) {
    throw new Error('ID della issue non trovato nella descrizione della pull request.');
    }
    const issueId = parseInt(issueMatch[1], 10);

    const issueResponse = await octokit.issues.get({
    owner: repoOwner,
    repo: repoName,
    issue_number: issueId
    });

    const issueBody = issueResponse.data.body;

    const idealTimeMatch = issueBody.match(/(\d+)\s*$/);
    if (!idealTimeMatch) {
    throw new Error('Tempo ideale non trovato nella descrizione della issue.');
    }
    const idealTime = parseInt(idealTimeMatch[1], 10);

    const roleMatch = issueBody.match(/([a-zA-Z\s]+)\s*\d+\s*$/);
    if (!roleMatch) {
    throw new Error('Ruolo non trovato nella descrizione della issue.');
    }
    const role = roleMatch[1].trim();
    const timeDifference = Math.abs(timeSpent - idealTime);
    const today = new Date();
    const todayTimestamp = today.getTime();

    const sheetResponse = await sheets.spreadsheets.values.get({
    spreadsheetId,
    range: 'Sheet1'
    });

    const rows = sheetResponse.data.values;
    const headerRow = rows[2];                                        //DA TENERE CONTO

    let dateColumnIndex = -1;
    let startTimestamp;
    let endTimestamp;
    for (let i = 2; i < headerRow.length; i++) { // Saltiamo l'intestazione della prima e della seconda colonna (ruoli e bianca)
        const range = headerRow[i].trim();
        const [start, end] = range.split('|').map(d => d.trim());

        startTimestamp = new Date(start.split('-').reverse().join('-')).getTime();
        endTimestamp = new Date(end.split('-').reverse().join('-')).getTime();
        console.log(`start: ${startTimestamp}`);
        console.log(`end: ${endTimestamp}`);
        console.log(`today: ${todayTimestamp}`);

        if (todayTimestamp >= startTimestamp && todayTimestamp <= endTimestamp) {
            dateColumnIndex = i;
            break;
        }
    }

    if (dateColumnIndex === -1) {
        throw new Error(`Nessuna colonna trovata per la data corrente ${today.toLocaleDateString()}.\nstart: ${startTimestamp}\nend: ${endTimestamp}\ntoday: ${todayTimestamp}`);
    }

    const roleRowIndex = rows.findIndex(row => row[0] === role);
    if (roleRowIndex === -1) {
    throw new Error(`Riga per il ruolo ${role} non trovata.`);
    }

    const range = `Sheet1!${String.fromCharCode(65 + dateColumnIndex)}${roleRowIndex + 1}`;
    await sheets.spreadsheets.values.update({
    spreadsheetId,
    range,
    valueInputOption: 'RAW',
    requestBody: {
        values: [[timeSpent]]
    }
    });

    console.log(`Aggiornato il foglio con la differenza di ${timeDifference} ore per il ruolo ${role} alla data ${todayTimestamp}.`);
})().catch(error => {
    console.error(error);
    process.exit(1);
});
