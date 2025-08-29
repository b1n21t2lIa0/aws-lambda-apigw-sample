include "root" { path = find_in_parent_folders() }
include "env"  { path = "${get_parent_terragrunt_dir()}/_env.hcl" }

terraform {
  source = "${get_repo_root()}/infra/modules/apigw_lambda_proxy"
}

dependencies {
  paths = ["../02-lambda"]
}

inputs = {
  name       = "${get_input("project")}-api"
  lambda_arn = dependency("../02-lambda").outputs.lambda_arn
}
