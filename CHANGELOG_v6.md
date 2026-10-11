# v6 changes

- Moved detailed live pipeline trace out of the user-facing Streamlit page into a backend JSONL audit file under `logs/pipeline_trace.jsonl`.
- Removed technical traceback details from the user-facing error panel.
- Added opt-out via `SMARTRECIPE_TRACE_ENABLED=false`; local trace files are Git-ignored.
- Expanded fixed assessment cases to nine cases.
- Added diet compliance, candidate existence and hard-constraint metrics and an aggregate summary JSON generated from actual experiment runs.
- Added trace writer unit tests and documentation.
- Did not invent results, AI calls, or human ratings.
