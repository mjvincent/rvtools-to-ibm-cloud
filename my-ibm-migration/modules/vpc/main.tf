
resource "ibm_is_vpc" "vpc" {
  name = "migration-vpc"
}

resource "ibm_is_subnet" "subnet" {
  name            = "migration-subnet"
  vpc             = ibm_is_vpc.vpc.id
  zone            = "us-south-1"
  ipv4_cidr_block = "10.240.0.0/24"
}
