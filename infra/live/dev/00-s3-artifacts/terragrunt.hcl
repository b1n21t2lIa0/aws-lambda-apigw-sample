include "root" { path = find_in_parent_folders() }
include "env"  { path = "${get_parent_terragrunt_dir()}/_env.hcl" }

terraform {
  source = "${get_repo_root()}/infra/modules/s3_artifacts"
}

inputs = {
  bucket_name = get_input("artifacts_bucket")
}
