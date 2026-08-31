"""IQEA Chat Agent — isolated conversational front end.

Fully independent of the existing feature pages. Nothing here mutates or
imports the current panels; skills call the same backend `utils.*` functions
that the panels call, but through a thin service layer added later.
"""
