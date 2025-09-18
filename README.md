# Forespørgsler til Ejendomsbeskatning

This robot receives requests for information regarding property tax and debt.
Requests are made via OS2Forms and read from an Outlook Inbox.
The results are sent to the given list of receivers.

## Overall flow

The robot goes through the following steps:

1. Get email from OS2Forms
2. Lookup address in Structura. Multiple properties might be found.
3. Find the property owners in Structura based on the email.
4. Find frozen debt in Structura.
5. Find tax information in Structura.
6. Find debt of each owner in SAP.
7. Upload email and results to GO case.
8. Send result to case worker including GO case number.

## Arguments

The robot expects an input formatted as a json object:

```json
{
    "receivers": [
        "abc@email.com"
    ],
    "doc_database_path": "C:\\database.db"
}
```

Receivers: A list of emails to send the result to.

## Troubleshooting

The robot is purely information seeking and therefore most errors are inconsequential.

Most errors happen due to instability in Structura and GO.

Some errors happen because the OS2Forms form is filled incorrectly.

- Incorrect property address. (The form validates against official addresses, but they might not be valid for other reasons.)
- Incorrect owner names. (This will not throw an error but might give wrong results.)
