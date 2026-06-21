- [x] Inspect repository structure and identify likely failure points (Postgres-only DB layer + model path assumptions)
- [ ] Inspect runtime error by running Streamlit and capturing traceback
- [ ] Fix prediction page model path loading (relative to repo) so it finds .pkl files reliably
- [ ] Make prediction page fail gracefully if DB is not reachable (show Streamlit error, not crash)
- [ ] If DB is the blocker: add SQLite fallback for local dev (based on shallom_auth.sqlite3)
- [ ] Run `streamlit run app.py` and verify the app loads + prediction page works
- [ ] Update any other pages if they assume Postgres but local uses SQLite


