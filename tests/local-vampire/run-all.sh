#!/usr/bin/env bash
# Run every BZ scenario through Vampire and report pass/fail.
#
# Pass criterion:
#   *.p files matching *-neg.p must produce "SZS status CounterSatisfiable"
#   all other *.p files must produce "SZS status Theorem"
#
# Requires: vampire on PATH (brew install vampire, or download a release
# binary from https://github.com/vprover/vampire/releases).
#
# Usage:
#   ./run-all.sh
#   ./run-all.sh -v        # also prints the proof body for each pass
#
# Exit code: 0 if every scenario matched its expected verdict, 1 otherwise.

set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

VERBOSE=0
[[ "${1:-}" == "-v" ]] && VERBOSE=1

if ! command -v vampire >/dev/null 2>&1; then
  echo "ERROR: vampire not on PATH. Install with: brew install vampire" >&2
  exit 2
fi

pass=0
fail=0
failed_files=()

shopt -s nullglob
for problem in *.p; do
  if [[ "$problem" == *-neg.p ]]; then
    expected="CounterSatisfiable"
  else
    expected="Theorem"
  fi

  output="$(vampire --proof tptp -t 60 "$problem" 2>&1)"
  status_line="$(echo "$output" | grep -E "^% SZS status" | head -1)"

  if echo "$status_line" | grep -q "$expected"; then
    printf "  PASS  %-40s  %s\n" "$problem" "$status_line"
    pass=$((pass+1))
    if [[ $VERBOSE -eq 1 ]]; then
      echo "$output" | sed 's/^/      /'
      echo
    fi
  else
    printf "  FAIL  %-40s  expected %s, got: %s\n" "$problem" "$expected" "$status_line"
    fail=$((fail+1))
    failed_files+=("$problem")
  fi
done

echo
echo "  $pass passed, $fail failed"
if [[ $fail -gt 0 ]]; then
  echo "  failed: ${failed_files[*]}"
  exit 1
fi
exit 0
