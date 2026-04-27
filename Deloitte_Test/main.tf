
module "vpc" {
  source = "./modules/vpc"
}

module "storage" {
  source = "./modules/storage"
}

module "vsi" {
  source = "./modules/vsi"
  vpc_id = module.vpc.vpc_id
}
