#!/bin/sh
set -eu

clients=${1:?client map required}
conntrack=${2:-/proc/net/nf_conntrack}
output=${3:-/var/run/wificalling-gateway/status.json}
tmp="${output}.tmp.$$"
trap 'rm -f "$tmp"' EXIT HUP INT TERM

now=$(date +%s)
awk -F '|' -v now="$now" '
function q(s, x) { x=s; gsub(/\\/,"\\\\",x); gsub(/\"/,"\\\"",x); return "\"" x "\"" }
FNR==NR { if ($1!="" && $2!="") { n++; label[n]=$1; ip[n]=$2; node[n]=$3 } next }
{
  line=$0
  for (i=1;i<=n;i++) {
    if (line !~ ("src=" ip[i] " ")) continue
    if (match(line,/dst=[0-9.]+/)) { dst=substr(line,RSTART+4,RLENGTH-4) }
    is500=(line ~ /dport=500 /); is4500=(line ~ /dport=4500 /)
    if (!is500 && !is4500) continue
    if (is500 && state[i]<1) state[i]=1
    if (is4500 && state[i]<2) state[i]=2
    if (is4500 && line ~ /\[ASSURED\]/) { state[i]=3; assured[i]=1 }
    epdg[i]=dst
    count=0; rest=line
    while (match(rest,/packets=[0-9]+/)) {
      val=substr(rest,RSTART+8,RLENGTH-8)+0
      count++
      if (count==1) sent[i]=val; else if(count==2) reply[i]=val
      rest=substr(rest,RSTART+RLENGTH)
    }
  }
}
END {
  print "{\"generated_at\":" now ",\"disclaimer\":\"Network evidence only; carrier IMS activation is not confirmed.\",\"devices\":["
  for(i=1;i<=n;i++) {
    s=(state[i]==3 && sent[i]+reply[i]>=100?"active_traffic":state[i]==3?"likely_registered":state[i]==2?"nat_t_seen":state[i]==1?"negotiating":"no_session")
    printf "%s{\"label\":%s,\"ip\":%s,\"node\":%s,\"state\":%s,\"epdg_ip\":%s,\"assured\":%s,\"sent_packets\":%d,\"reply_packets\":%d}", (i>1?",":""), q(label[i]), q(ip[i]), q(node[i]), q(s), q(epdg[i]), (assured[i]?"true":"false"), sent[i]+0, reply[i]+0
  }
  print "]}"
}
' "$clients" "$conntrack" > "$tmp"
chmod 600 "$tmp"
mv "$tmp" "$output"
trap - EXIT HUP INT TERM
