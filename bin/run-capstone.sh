#!/usr/bin/env bash
set -Eeuo pipefail
project_dir=$(mktemp -d /home/project/accounts-capstone.XXXXXX)
evidence_dir="$project_dir/evidence"
mkdir -p "$evidence_dir"
trap 'echo "Stopped at line $LINENO. Evidence: $evidence_dir" >&2' ERR
namespace=$(oc project -q)
[ "$namespace" = sn-labs-shayanobrohi ] || { echo "Use your Skills Network namespace."; exit 1; }
git clone https://github.com/shyrradev/devops-capstone-project.git "$project_dir/repo"
cd "$project_dir/repo"
if ! oc get secret accounts-db >/dev/null 2>&1; then
  python3 -c 'import secrets;print(secrets.token_urlsafe(32),end="")' > "$project_dir/db-password"
  chmod 600 "$project_dir/db-password"
  oc create secret generic accounts-db --from-file=password="$project_dir/db-password"
  rm "$project_dir/db-password"
fi
oc apply -f deploy/postgres.yaml
oc rollout status deployment/accounts-db --timeout=240s
oc apply -f tekton/tasks.yaml
oc apply -f tekton/pvc.yaml
oc apply -f tekton/pipeline.yaml
cat > "$project_dir/run.yaml" <<RUN
apiVersion: tekton.dev/v1beta1
kind: PipelineRun
metadata:
  generateName: accounts-cd-run-
spec:
  serviceAccountName: pipeline
  pipelineRef:
    name: accounts-cd
  timeout: 30m
  params:
    - name: image-url
      value: image-registry.openshift-image-registry.svc:5000/$namespace/accounts:latest
  workspaces:
    - name: shared-workspace
      persistentVolumeClaim:
        claimName: accounts-source-pvc
RUN
run_name=$(oc create -f "$project_dir/run.yaml" -o jsonpath='{.metadata.name}')
printf 'PipelineRun: %s\n' "$run_name"
tkn pipelinerun logs "$run_name" -f 2>&1 | tee "$evidence_dir/pipelinerun.txt"
[ "$(oc get pipelinerun "$run_name" -o jsonpath='{.status.conditions[0].status}')" = True ] || { echo "Pipeline failed; send the output."; exit 1; }
{ oc get deployment/accounts service/accounts -o wide; oc get pods,replicasets -l app=accounts -o wide; } | tee "$evidence_dir/kube-deploy-accounts"
route_host=$(oc get route accounts -o jsonpath='{.spec.host}')
curl --fail --retry 8 --retry-delay 3 "https://$route_host/" | tee "$evidence_dir/kube-app-output"
printf '\nApplication: https://%s\nEvidence directory: %s\n' "$route_host" "$evidence_dir"
printf '\nPaste pipelinerun.txt and kube-deploy-accounts here.\n'
