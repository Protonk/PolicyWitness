#!/bin/zsh
# wrap.sh PROFILE OP ACTION PATH...
# Prediction: sandbox_check against a live /bin/sleep started under PROFILE by sandbox-exec.
# Attempt: a fresh process started under PROFILE by sandbox-exec performs ACTION on each PATH.
B=${0:h}
P=$1; OP=$2; ACT=$3; shift 3
/usr/bin/sandbox-exec -f "$P" /bin/sleep 20 &
pid=$!
n=0
until [[ "$(/bin/ps -o comm= -p $pid)" == "/bin/sleep" ]]; do n=$((n+1)); if (( n > 200000 )); then echo "holder never reached sleep" >&2; kill $pid; exit 3; fi; done
echo "# holder pid=$pid profile=${P:t}"
"$B/chk" $pid "$OP" "$@"
kill $pid; wait $pid 2>/dev/null
/usr/bin/sandbox-exec -f "$P" "$B/try" "$ACT" "$@"
echo "# sandbox-exec exit=$?"
