#!/usr/bin/env bash
set -uo pipefail
PASS=0; FAIL=0
check() {
 local desc="$1" expected="$2" actual="$3"
 if [[ "$actual" == "$expected" ]]; then printf '  [OK] %s\n' "$desc"; PASS=$((PASS+1));
 else printf '  [FAIL] %s (expected %s got %s)\n' "$desc" "$expected" "$actual"; FAIL=$((FAIL+1)); fi
}
echo "Audit: $(hostname -f), $(date -Is)"
echo '[1] SSH'
SSHD="$(sudo sshd -T)"
value() { awk -v k="$1" '$1==k {print $2;exit}' <<<"$SSHD"; }
check 'Root login disabled' no "$(value permitrootlogin)"
check 'Password authentication disabled' no "$(value passwordauthentication)"
check 'Nonstandard SSH port' yes "$([[ $(value port) =~ ^[0-9]+$ && $(value port) != 22 ]] && echo yes || echo no)"
check 'MaxAuthTries' 3 "$(value maxauthtries)"
echo '[2] Firewall'
check 'UFW active' active "$(sudo env LC_ALL=C ufw status | awk '/^Status:/{print $2}')"
check 'Incoming denied' yes "$(sudo env LC_ALL=C ufw status verbose | grep -q 'Default: deny (incoming)' && echo yes || echo no)"
echo '[3] Accounts'
awk -F: '$3>=1000 && $3<65534 {printf "    %s (uid=%s)\n",$1,$3}' /etc/passwd
if [[ ${AUDIT_STAGE:-6} -ge 6 ]]; then
 echo '[4] Web server'
 check 'Nginx active' active "$(systemctl is-active nginx)"
 check 'Nginx config valid' 0 "$(sudo nginx -t >/dev/null 2>&1; echo $?)"
 check 'Certificate valid for threshold' 0 "$(openssl x509 -in /etc/ssl/certs/devops.crt -checkend "${AUDIT_CERT_SECONDS:-2592000}" -noout >/dev/null 2>&1; echo $?)"
 check 'No world-writable site files' '' "$(find /var/www/devops-site -perm -o+w -print)"
 check 'Private key permissions' 600 "$(sudo stat -c '%a' /etc/ssl/private/devops.key)"
fi
if [[ ${AUDIT_STAGE:-6} -ge 7 ]]; then
 echo '[5] Containers'
 check 'Docker active' active "$(systemctl is-active docker)"
 DB_ID="$(docker compose --project-directory "$HOME/app" ps -q db)"
 check 'Database healthy' healthy "$(docker inspect -f '{{.State.Health.Status}}' "$DB_ID" 2>/dev/null)"
 check 'No public app or database listeners' '' "$(ss -H -tln | awk '$4 ~ /:(5000|5432)$/ && $4 !~ /^127\.0\.0\.1:/ {print $4}')"
 check 'App environment permissions' 600 "$(stat -c '%a' "$HOME/app/.env")"
fi
printf 'Passed: %s; failed: %s\n' "$PASS" "$FAIL"
[[ $FAIL -eq 0 ]]
