ENV ?= dev

plan:
	cd infra/live/$(ENV) && terragrunt run-all plan --terragrunt-non-interactive

apply:
	cd infra/live/$(ENV) && terragrunt run-all apply --terragrunt-non-interactive --auto-approve

fmt:
	terragrunt hclfmt --terragrunt-working-dir infra/live
	terraform -chdir=infra/modules fmt -recursive
