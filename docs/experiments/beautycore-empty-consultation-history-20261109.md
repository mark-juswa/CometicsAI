# Empty consultation history diagnosis, 9 November 2026

Status: VERIFIED read-only database state and inspected read/write boundaries. No code, schema, account, image or consultation was changed.

The configured database returned these counts:

```json
{"archived_consultations":0,"archived_reference_photos":0,"archived_consultation_results":0,"existing_generation_records":61,"demo_client_consultations":0}
```

Generation categories:

```json
[{"source":"consultation","records":7,"saved_looks":7},{"source":"legacy","records":51,"saved_looks":0},{"source":"manual","records":3,"saved_looks":3}]
```

These are database-wide counts, not an assertion that every record belongs to the current browser account. Consultation History reads owner-scoped `client_consultations`, with associated reference/result rows. My Saved Looks reads saved generation rows. The seven saved consultation images are therefore not seven archived conversations; no archive session exists to list or reconstruct from them. The current archive wrapper stores accepted signed-in consultation responses independently of explicit Save Look.

The current code implements future archiving, but this read-only audit does not establish when or through which deployed version those seven images were saved. They may predate the archive feature or have been saved through an older running build. No successful new session or live AI invocation was created to test that historical distinction. Expired, previously unpersisted conversation messages cannot be inferred from generated images. The previous UI work is local and was not deployed to the public site.

The first count request failed because sandbox DNS could not resolve the database endpoint. The same read-only query completed through the approved elevated command. A second read-only aggregate distinguished saved consultation images from manual and legacy generation rows. No private images, prompts, transcripts, credentials or database connection strings were printed.
