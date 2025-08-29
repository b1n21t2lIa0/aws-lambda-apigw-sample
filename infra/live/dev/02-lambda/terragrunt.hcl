include "root" { path = find_in_parent_folders() }
include "env"  { path = "${get_parent_terragrunt_dir()}/_env.hcl" }

terraform {
  source = "${get_repo_root()}/infra/modules/lambda_function"
}

dependencies {
  paths = [
    "../00-s3-artifacts",
    "../01-iam-role"
  ]
}

locals {
  fn          = "hello_world"
  manifest    = get_input("manifest")
  artifact    = try(local.manifest[local.fn], null)
  s3_bucket   = try(local.artifact.s3_bucket, get_input("artifacts_bucket"))
  s3_key      = try(local.artifact.s3_key, "")
}

inputs = {
  function_name = "${get_input("project")}-${local.fn}"
  role_arn      = dependency("../01-iam-role").outputs.role_arn
  s3_bucket     = local.s3_bucket
  s3_key        = local.s3_key
  runtime       = "python3.12"
  handler       = "app.handler"
  env           = { STAGE = get_input("stage") }
  tags          = get_input("tags")
}
