locals {
  stage = "dev"
}

inputs = {
  stage = local.stage
  tags  = merge(
    { env = local.stage },
    { owner = "platform" }
  )
}
