# Forespørgsler til Ejendomsbeskatning

This robot receives requests for information regarding property tax and debt.
Requests are made via OS2Forms and read from an Outlook Inbox.
The results are sent to the given list of receivers.

## Arguments

The robot expects an input formatted as a json object:

```json
{
    "receivers": [
        "abc@email.com"
    ]
}
```

Receivers: A list of emails to send the result to.
