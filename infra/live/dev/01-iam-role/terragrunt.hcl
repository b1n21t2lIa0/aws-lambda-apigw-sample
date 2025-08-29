include "root" { path = find_in_parent_folders() }
include "env"  { path = "${get_parent_terragrunt_dir()}/_env.hcl" }

terraform {
  source = "${get_repo_root()}/infra/modules/iam_role_lambda"
}

dependencies {
  paths = ["../00-s3-artifacts"]
}

inputs = {
  name = "${get_input("project")}-hello_world-lambda-role"
  tags = get_input("tags")
}
