# ClariFin OS — Verification Runtime package.
#
# Makes `runtime` an explicit, importable package so that
# `from runtime.foundation.verification.*` resolves consistently and mypy
# no longer mis-maps modules under two root names.
