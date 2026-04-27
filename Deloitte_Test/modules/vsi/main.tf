##############################################################################
# Virtual Server Instance: 
# Migrated from VMware via RVTools
##############################################################################

resource "ibm_is_instance" "ad01-va-hicloud" {
  name    = "ad01-va-hicloud"
  image   = var.image_id
  profile = "cx2-4x8"

  primary_network_interface {
    subnet = ibm_is_subnet.subnet.id
  }

  vpc  = ibm_is_vpc.vpc.id
  zone = var.ibm_zone
  keys = [data.ibm_is_ssh_key.ssh_key.id]
}##############################################################################
# Virtual Server Instance: 
# Migrated from VMware via RVTools
##############################################################################

resource "ibm_is_instance" "ad02-va-hicloud" {
  name    = "ad02-va-hicloud"
  image   = var.image_id
  profile = "cx2-4x8"

  primary_network_interface {
    subnet = ibm_is_subnet.subnet.id
  }

  vpc  = ibm_is_vpc.vpc.id
  zone = var.ibm_zone
  keys = [data.ibm_is_ssh_key.ssh_key.id]
}##############################################################################
# Virtual Server Instance: 
# Migrated from VMware via RVTools
##############################################################################

resource "ibm_is_instance" "adminlinuxutilityserver-va-hicloud" {
  name    = "adminlinuxutilityserver-va-hicloud"
  image   = var.image_id
  profile = "cx2-2x4"

  primary_network_interface {
    subnet = ibm_is_subnet.subnet.id
  }

  vpc  = ibm_is_vpc.vpc.id
  zone = var.ibm_zone
  keys = [data.ibm_is_ssh_key.ssh_key.id]
}##############################################################################
# Virtual Server Instance: 
# Migrated from VMware via RVTools
##############################################################################

resource "ibm_is_instance" "adminwindowsutilityserver-va-hicloud" {
  name    = "adminwindowsutilityserver-va-hicloud"
  image   = var.image_id
  profile = "bx2-4x16"

  primary_network_interface {
    subnet = ibm_is_subnet.subnet.id
  }

  vpc  = ibm_is_vpc.vpc.id
  zone = var.ibm_zone
  keys = [data.ibm_is_ssh_key.ssh_key.id]
}##############################################################################
# Virtual Server Instance: 
# Migrated from VMware via RVTools
##############################################################################

resource "ibm_is_instance" "adnsva-primary1" {
  name    = "adnsva-primary1"
  image   = var.image_id
  profile = "bx2-2x8"

  primary_network_interface {
    subnet = ibm_is_subnet.subnet.id
  }

  vpc  = ibm_is_vpc.vpc.id
  zone = var.ibm_zone
  keys = [data.ibm_is_ssh_key.ssh_key.id]
}##############################################################################
# Virtual Server Instance: 
# Migrated from VMware via RVTools
##############################################################################

resource "ibm_is_instance" "adnsva-primary2" {
  name    = "adnsva-primary2"
  image   = var.image_id
  profile = "bx2-2x8"

  primary_network_interface {
    subnet = ibm_is_subnet.subnet.id
  }

  vpc  = ibm_is_vpc.vpc.id
  zone = var.ibm_zone
  keys = [data.ibm_is_ssh_key.ssh_key.id]
}##############################################################################
# Virtual Server Instance: 
# Migrated from VMware via RVTools
##############################################################################

resource "ibm_is_instance" "archive1-va-hicloud" {
  name    = "archive1-va-hicloud"
  image   = var.image_id
  profile = "cx2-2x2"

  primary_network_interface {
    subnet = ibm_is_subnet.subnet.id
  }

  vpc  = ibm_is_vpc.vpc.id
  zone = var.ibm_zone
  keys = [data.ibm_is_ssh_key.ssh_key.id]
}##############################################################################
# Virtual Server Instance: 
# Migrated from VMware via RVTools
##############################################################################

resource "ibm_is_instance" "backups-va-hicloud" {
  name    = "backups-va-hicloud"
  image   = var.image_id
  profile = "cx2-2x4"

  primary_network_interface {
    subnet = ibm_is_subnet.subnet.id
  }

  vpc  = ibm_is_vpc.vpc.id
  zone = var.ibm_zone
  keys = [data.ibm_is_ssh_key.ssh_key.id]
}##############################################################################
# Virtual Server Instance: 
# Migrated from VMware via RVTools
##############################################################################

resource "ibm_is_instance" "ca01-va-hicloud" {
  name    = "ca01-va-hicloud"
  image   = var.image_id
  profile = "cx2-4x8"

  primary_network_interface {
    subnet = ibm_is_subnet.subnet.id
  }

  vpc  = ibm_is_vpc.vpc.id
  zone = var.ibm_zone
  keys = [data.ibm_is_ssh_key.ssh_key.id]
}##############################################################################
# Virtual Server Instance: 
# Migrated from VMware via RVTools
##############################################################################

resource "ibm_is_instance" "carbonblack-sensor-gateway-primary" {
  name    = "carbonblack-sensor-gateway-primary"
  image   = var.image_id
  profile = "cx2-8x8"

  primary_network_interface {
    subnet = ibm_is_subnet.subnet.id
  }

  vpc  = ibm_is_vpc.vpc.id
  zone = var.ibm_zone
  keys = [data.ibm_is_ssh_key.ssh_key.id]
}##############################################################################
# Virtual Server Instance: 
# Migrated from VMware via RVTools
##############################################################################

resource "ibm_is_instance" "carbonblack-workoad-primary" {
  name    = "carbonblack-workoad-primary"
  image   = var.image_id
  profile = "cx2-4x4"

  primary_network_interface {
    subnet = ibm_is_subnet.subnet.id
  }

  vpc  = ibm_is_vpc.vpc.id
  zone = var.ibm_zone
  keys = [data.ibm_is_ssh_key.ssh_key.id]
}##############################################################################
# Virtual Server Instance: 
# Migrated from VMware via RVTools
##############################################################################

resource "ibm_is_instance" "core01" {
  name    = "core01"
  image   = var.image_id
  profile = "bx2-8x32"

  primary_network_interface {
    subnet = ibm_is_subnet.subnet.id
  }

  vpc  = ibm_is_vpc.vpc.id
  zone = var.ibm_zone
  keys = [data.ibm_is_ssh_key.ssh_key.id]
}##############################################################################
# Virtual Server Instance: 
# Migrated from VMware via RVTools
##############################################################################

resource "ibm_is_instance" "core02" {
  name    = "core02"
  image   = var.image_id
  profile = "bx2-8x32"

  primary_network_interface {
    subnet = ibm_is_subnet.subnet.id
  }

  vpc  = ibm_is_vpc.vpc.id
  zone = var.ibm_zone
  keys = [data.ibm_is_ssh_key.ssh_key.id]
}##############################################################################
# Virtual Server Instance: 
# Migrated from VMware via RVTools
##############################################################################

resource "ibm_is_instance" "datapower-template" {
  name    = "datapower-template"
  image   = var.image_id
  profile = "mx2-2x16"

  primary_network_interface {
    subnet = ibm_is_subnet.subnet.id
  }

  vpc  = ibm_is_vpc.vpc.id
  zone = var.ibm_zone
  keys = [data.ibm_is_ssh_key.ssh_key.id]
}##############################################################################
# Virtual Server Instance: 
# Migrated from VMware via RVTools
##############################################################################

resource "ibm_is_instance" "datapower-dev-va-hicloud" {
  name    = "datapower-dev-va-hicloud"
  image   = var.image_id
  profile = "mx2-2x16"

  primary_network_interface {
    subnet = ibm_is_subnet.subnet.id
  }

  vpc  = ibm_is_vpc.vpc.id
  zone = var.ibm_zone
  keys = [data.ibm_is_ssh_key.ssh_key.id]
}##############################################################################
# Virtual Server Instance: 
# Migrated from VMware via RVTools
##############################################################################

resource "ibm_is_instance" "datapower-prod-va-hicloud" {
  name    = "datapower-prod-va-hicloud"
  image   = var.image_id
  profile = "mx2-2x16"

  primary_network_interface {
    subnet = ibm_is_subnet.subnet.id
  }

  vpc  = ibm_is_vpc.vpc.id
  zone = var.ibm_zone
  keys = [data.ibm_is_ssh_key.ssh_key.id]
}##############################################################################
# Virtual Server Instance: 
# Migrated from VMware via RVTools
##############################################################################

resource "ibm_is_instance" "datapower-sit-va-hicloud" {
  name    = "datapower-sit-va-hicloud"
  image   = var.image_id
  profile = "mx2-2x16"

  primary_network_interface {
    subnet = ibm_is_subnet.subnet.id
  }

  vpc  = ibm_is_vpc.vpc.id
  zone = var.ibm_zone
  keys = [data.ibm_is_ssh_key.ssh_key.id]
}##############################################################################
# Virtual Server Instance: 
# Migrated from VMware via RVTools
##############################################################################

resource "ibm_is_instance" "datapower-stg-va-hicloud" {
  name    = "datapower-stg-va-hicloud"
  image   = var.image_id
  profile = "bx2-4x16"

  primary_network_interface {
    subnet = ibm_is_subnet.subnet.id
  }

  vpc  = ibm_is_vpc.vpc.id
  zone = var.ibm_zone
  keys = [data.ibm_is_ssh_key.ssh_key.id]
}##############################################################################
# Virtual Server Instance: 
# Migrated from VMware via RVTools
##############################################################################

resource "ibm_is_instance" "datapower1-prod-va-hicloud" {
  name    = "datapower1-prod-va-hicloud"
  image   = var.image_id
  profile = "mx2-2x16"

  primary_network_interface {
    subnet = ibm_is_subnet.subnet.id
  }

  vpc  = ibm_is_vpc.vpc.id
  zone = var.ibm_zone
  keys = [data.ibm_is_ssh_key.ssh_key.id]
}##############################################################################
# Virtual Server Instance: 
# Migrated from VMware via RVTools
##############################################################################

resource "ibm_is_instance" "datapower1-stg-va-hicloud" {
  name    = "datapower1-stg-va-hicloud"
  image   = var.image_id
  profile = "bx2-4x16"

  primary_network_interface {
    subnet = ibm_is_subnet.subnet.id
  }

  vpc  = ibm_is_vpc.vpc.id
  zone = var.ibm_zone
  keys = [data.ibm_is_ssh_key.ssh_key.id]
}##############################################################################
# Virtual Server Instance: 
# Migrated from VMware via RVTools
##############################################################################

resource "ibm_is_instance" "devutilwin01-dev-va-hicloud" {
  name    = "devutilwin01-dev-va-hicloud"
  image   = var.image_id
  profile = "cx2-4x8"

  primary_network_interface {
    subnet = ibm_is_subnet.subnet.id
  }

  vpc  = ibm_is_vpc.vpc.id
  zone = var.ibm_zone
  keys = [data.ibm_is_ssh_key.ssh_key.id]
}##############################################################################
# Virtual Server Instance: 
# Migrated from VMware via RVTools
##############################################################################

resource "ibm_is_instance" "devutilwin02-sit-va-hicloud" {
  name    = "devutilwin02-sit-va-hicloud"
  image   = var.image_id
  profile = "cx2-4x8"

  primary_network_interface {
    subnet = ibm_is_subnet.subnet.id
  }

  vpc  = ibm_is_vpc.vpc.id
  zone = var.ibm_zone
  keys = [data.ibm_is_ssh_key.ssh_key.id]
}##############################################################################
# Virtual Server Instance: 
# Migrated from VMware via RVTools
##############################################################################

resource "ibm_is_instance" "devutilwin03-stg-va-hicloud" {
  name    = "devutilwin03-stg-va-hicloud"
  image   = var.image_id
  profile = "cx2-4x8"

  primary_network_interface {
    subnet = ibm_is_subnet.subnet.id
  }

  vpc  = ibm_is_vpc.vpc.id
  zone = var.ibm_zone
  keys = [data.ibm_is_ssh_key.ssh_key.id]
}##############################################################################
# Virtual Server Instance: 
# Migrated from VMware via RVTools
##############################################################################

resource "ibm_is_instance" "devutilwin04-prod-va-hicloud" {
  name    = "devutilwin04-prod-va-hicloud"
  image   = var.image_id
  profile = "bx2-4x12"

  primary_network_interface {
    subnet = ibm_is_subnet.subnet.id
  }

  vpc  = ibm_is_vpc.vpc.id
  zone = var.ibm_zone
  keys = [data.ibm_is_ssh_key.ssh_key.id]
}##############################################################################
# Virtual Server Instance: 
# Migrated from VMware via RVTools
##############################################################################

resource "ibm_is_instance" "devutilwin10-va-hicloud" {
  name    = "devutilwin10-va-hicloud"
  image   = var.image_id
  profile = "cx2-4x8"

  primary_network_interface {
    subnet = ibm_is_subnet.subnet.id
  }

  vpc  = ibm_is_vpc.vpc.id
  zone = var.ibm_zone
  keys = [data.ibm_is_ssh_key.ssh_key.id]
}##############################################################################
# Virtual Server Instance: 
# Migrated from VMware via RVTools
##############################################################################

resource "ibm_is_instance" "dns1-va-hicloud" {
  name    = "dns1-va-hicloud"
  image   = var.image_id
  profile = "cx2-2x4"

  primary_network_interface {
    subnet = ibm_is_subnet.subnet.id
  }

  vpc  = ibm_is_vpc.vpc.id
  zone = var.ibm_zone
  keys = [data.ibm_is_ssh_key.ssh_key.id]
}##############################################################################
# Virtual Server Instance: 
# Migrated from VMware via RVTools
##############################################################################

resource "ibm_is_instance" "dns2-va-hicloud" {
  name    = "dns2-va-hicloud"
  image   = var.image_id
  profile = "cx2-2x4"

  primary_network_interface {
    subnet = ibm_is_subnet.subnet.id
  }

  vpc  = ibm_is_vpc.vpc.id
  zone = var.ibm_zone
  keys = [data.ibm_is_ssh_key.ssh_key.id]
}##############################################################################
# Virtual Server Instance: 
# Migrated from VMware via RVTools
##############################################################################

resource "ibm_is_instance" "duo-auth-proxy-va-hicloud" {
  name    = "duo-auth-proxy-va-hicloud"
  image   = var.image_id
  profile = "cx2-2x4"

  primary_network_interface {
    subnet = ibm_is_subnet.subnet.id
  }

  vpc  = ibm_is_vpc.vpc.id
  zone = var.ibm_zone
  keys = [data.ibm_is_ssh_key.ssh_key.id]
}##############################################################################
# Virtual Server Instance: 
# Migrated from VMware via RVTools
##############################################################################

resource "ibm_is_instance" "fg500d-backups-va-hicloud" {
  name    = "fg500d-backups-va-hicloud"
  image   = var.image_id
  profile = "cx2-2x2"

  primary_network_interface {
    subnet = ibm_is_subnet.subnet.id
  }

  vpc  = ibm_is_vpc.vpc.id
  zone = var.ibm_zone
  keys = [data.ibm_is_ssh_key.ssh_key.id]
}##############################################################################
# Virtual Server Instance: 
# Migrated from VMware via RVTools
##############################################################################

resource "ibm_is_instance" "gitlab-va-hicloud" {
  name    = "gitlab-va-hicloud"
  image   = var.image_id
  profile = "cx2-4x8"

  primary_network_interface {
    subnet = ibm_is_subnet.subnet.id
  }

  vpc  = ibm_is_vpc.vpc.id
  zone = var.ibm_zone
  keys = [data.ibm_is_ssh_key.ssh_key.id]
}##############################################################################
# Virtual Server Instance: 
# Migrated from VMware via RVTools
##############################################################################

resource "ibm_is_instance" "ilmt-va-hicloud" {
  name    = "ilmt-va-hicloud"
  image   = var.image_id
  profile = "bx2-4x16"

  primary_network_interface {
    subnet = ibm_is_subnet.subnet.id
  }

  vpc  = ibm_is_vpc.vpc.id
  zone = var.ibm_zone
  keys = [data.ibm_is_ssh_key.ssh_key.id]
}##############################################################################
# Virtual Server Instance: 
# Migrated from VMware via RVTools
##############################################################################

resource "ibm_is_instance" "isam-template" {
  name    = "isam-template"
  image   = var.image_id
  profile = "bx2-1x4"

  primary_network_interface {
    subnet = ibm_is_subnet.subnet.id
  }

  vpc  = ibm_is_vpc.vpc.id
  zone = var.ibm_zone
  keys = [data.ibm_is_ssh_key.ssh_key.id]
}##############################################################################
# Virtual Server Instance: 
# Migrated from VMware via RVTools
##############################################################################

resource "ibm_is_instance" "isam-dev-va-hicloud" {
  name    = "isam-dev-va-hicloud"
  image   = var.image_id
  profile = "mx2-1x32"

  primary_network_interface {
    subnet = ibm_is_subnet.subnet.id
  }

  vpc  = ibm_is_vpc.vpc.id
  zone = var.ibm_zone
  keys = [data.ibm_is_ssh_key.ssh_key.id]
}##############################################################################
# Virtual Server Instance: 
# Migrated from VMware via RVTools
##############################################################################

resource "ibm_is_instance" "isam-prod-va-hicloud" {
  name    = "isam-prod-va-hicloud"
  image   = var.image_id
  profile = "mx2-4x32"

  primary_network_interface {
    subnet = ibm_is_subnet.subnet.id
  }

  vpc  = ibm_is_vpc.vpc.id
  zone = var.ibm_zone
  keys = [data.ibm_is_ssh_key.ssh_key.id]
}##############################################################################
# Virtual Server Instance: 
# Migrated from VMware via RVTools
##############################################################################

resource "ibm_is_instance" "isam-sit-va-hicloud" {
  name    = "isam-sit-va-hicloud"
  image   = var.image_id
  profile = "mx2-1x16"

  primary_network_interface {
    subnet = ibm_is_subnet.subnet.id
  }

  vpc  = ibm_is_vpc.vpc.id
  zone = var.ibm_zone
  keys = [data.ibm_is_ssh_key.ssh_key.id]
}##############################################################################
# Virtual Server Instance: 
# Migrated from VMware via RVTools
##############################################################################

resource "ibm_is_instance" "isam-stg-va-hicloud" {
  name    = "isam-stg-va-hicloud"
  image   = var.image_id
  profile = "cx2-2x4"

  primary_network_interface {
    subnet = ibm_is_subnet.subnet.id
  }

  vpc  = ibm_is_vpc.vpc.id
  zone = var.ibm_zone
  keys = [data.ibm_is_ssh_key.ssh_key.id]
}##############################################################################
# Virtual Server Instance: 
# Migrated from VMware via RVTools
##############################################################################

resource "ibm_is_instance" "isam1-prod-va-hicloud" {
  name    = "isam1-prod-va-hicloud"
  image   = var.image_id
  profile = "mx2-4x32"

  primary_network_interface {
    subnet = ibm_is_subnet.subnet.id
  }

  vpc  = ibm_is_vpc.vpc.id
  zone = var.ibm_zone
  keys = [data.ibm_is_ssh_key.ssh_key.id]
}##############################################################################
# Virtual Server Instance: 
# Migrated from VMware via RVTools
##############################################################################

resource "ibm_is_instance" "isam1-stg-va-hicloud" {
  name    = "isam1-stg-va-hicloud"
  image   = var.image_id
  profile = "cx2-2x4"

  primary_network_interface {
    subnet = ibm_is_subnet.subnet.id
  }

  vpc  = ibm_is_vpc.vpc.id
  zone = var.ibm_zone
  keys = [data.ibm_is_ssh_key.ssh_key.id]
}##############################################################################
# Virtual Server Instance: 
# Migrated from VMware via RVTools
##############################################################################

resource "ibm_is_instance" "isampa-dev-va-hicloud" {
  name    = "isampa-dev-va-hicloud"
  image   = var.image_id
  profile = "mx2-2x16"

  primary_network_interface {
    subnet = ibm_is_subnet.subnet.id
  }

  vpc  = ibm_is_vpc.vpc.id
  zone = var.ibm_zone
  keys = [data.ibm_is_ssh_key.ssh_key.id]
}##############################################################################
# Virtual Server Instance: 
# Migrated from VMware via RVTools
##############################################################################

resource "ibm_is_instance" "isamweb-prod-va-hicloud" {
  name    = "isamweb-prod-va-hicloud"
  image   = var.image_id
  profile = "bx2-2x8"

  primary_network_interface {
    subnet = ibm_is_subnet.subnet.id
  }

  vpc  = ibm_is_vpc.vpc.id
  zone = var.ibm_zone
  keys = [data.ibm_is_ssh_key.ssh_key.id]
}##############################################################################
# Virtual Server Instance: 
# Migrated from VMware via RVTools
##############################################################################

resource "ibm_is_instance" "isamweb-sit-va-hicloud" {
  name    = "isamweb-sit-va-hicloud"
  image   = var.image_id
  profile = "bx2-1x4"

  primary_network_interface {
    subnet = ibm_is_subnet.subnet.id
  }

  vpc  = ibm_is_vpc.vpc.id
  zone = var.ibm_zone
  keys = [data.ibm_is_ssh_key.ssh_key.id]
}##############################################################################
# Virtual Server Instance: 
# Migrated from VMware via RVTools
##############################################################################

resource "ibm_is_instance" "isamweb-stg-va-hicloud" {
  name    = "isamweb-stg-va-hicloud"
  image   = var.image_id
  profile = "bx2-2x8"

  primary_network_interface {
    subnet = ibm_is_subnet.subnet.id
  }

  vpc  = ibm_is_vpc.vpc.id
  zone = var.ibm_zone
  keys = [data.ibm_is_ssh_key.ssh_key.id]
}##############################################################################
# Virtual Server Instance: 
# Migrated from VMware via RVTools
##############################################################################

resource "ibm_is_instance" "isamweb1-prod-va-hicloud" {
  name    = "isamweb1-prod-va-hicloud"
  image   = var.image_id
  profile = "bx2-2x8"

  primary_network_interface {
    subnet = ibm_is_subnet.subnet.id
  }

  vpc  = ibm_is_vpc.vpc.id
  zone = var.ibm_zone
  keys = [data.ibm_is_ssh_key.ssh_key.id]
}##############################################################################
# Virtual Server Instance: 
# Migrated from VMware via RVTools
##############################################################################

resource "ibm_is_instance" "isamweb1-stg-va-hicloud" {
  name    = "isamweb1-stg-va-hicloud"
  image   = var.image_id
  profile = "bx2-2x8"

  primary_network_interface {
    subnet = ibm_is_subnet.subnet.id
  }

  vpc  = ibm_is_vpc.vpc.id
  zone = var.ibm_zone
  keys = [data.ibm_is_ssh_key.ssh_key.id]
}##############################################################################
# Virtual Server Instance: 
# Migrated from VMware via RVTools
##############################################################################

resource "ibm_is_instance" "isim-dev-va-hicloud" {
  name    = "isim-dev-va-hicloud"
  image   = var.image_id
  profile = "bx2-4x16"

  primary_network_interface {
    subnet = ibm_is_subnet.subnet.id
  }

  vpc  = ibm_is_vpc.vpc.id
  zone = var.ibm_zone
  keys = [data.ibm_is_ssh_key.ssh_key.id]
}##############################################################################
# Virtual Server Instance: 
# Migrated from VMware via RVTools
##############################################################################

resource "ibm_is_instance" "isim-prod-va-hicloud" {
  name    = "isim-prod-va-hicloud"
  image   = var.image_id
  profile = "bx2-4x16"

  primary_network_interface {
    subnet = ibm_is_subnet.subnet.id
  }

  vpc  = ibm_is_vpc.vpc.id
  zone = var.ibm_zone
  keys = [data.ibm_is_ssh_key.ssh_key.id]
}##############################################################################
# Virtual Server Instance: 
# Migrated from VMware via RVTools
##############################################################################

resource "ibm_is_instance" "isim-prod-va-hicloud-orgin" {
  name    = "isim-prod-va-hicloud-orgin"
  image   = var.image_id
  profile = "mx2-1x16"

  primary_network_interface {
    subnet = ibm_is_subnet.subnet.id
  }

  vpc  = ibm_is_vpc.vpc.id
  zone = var.ibm_zone
  keys = [data.ibm_is_ssh_key.ssh_key.id]
}##############################################################################
# Virtual Server Instance: 
# Migrated from VMware via RVTools
##############################################################################

resource "ibm_is_instance" "isim-sit-va-hicloud" {
  name    = "isim-sit-va-hicloud"
  image   = var.image_id
  profile = "bx2-4x16"

  primary_network_interface {
    subnet = ibm_is_subnet.subnet.id
  }

  vpc  = ibm_is_vpc.vpc.id
  zone = var.ibm_zone
  keys = [data.ibm_is_ssh_key.ssh_key.id]
}##############################################################################
# Virtual Server Instance: 
# Migrated from VMware via RVTools
##############################################################################

resource "ibm_is_instance" "isim-stg-va-hicloud" {
  name    = "isim-stg-va-hicloud"
  image   = var.image_id
  profile = "bx2-4x16"

  primary_network_interface {
    subnet = ibm_is_subnet.subnet.id
  }

  vpc  = ibm_is_vpc.vpc.id
  zone = var.ibm_zone
  keys = [data.ibm_is_ssh_key.ssh_key.id]
}##############################################################################
# Virtual Server Instance: 
# Migrated from VMware via RVTools
##############################################################################

resource "ibm_is_instance" "isim1-prod-va-hicloud" {
  name    = "isim1-prod-va-hicloud"
  image   = var.image_id
  profile = "bx2-4x16"

  primary_network_interface {
    subnet = ibm_is_subnet.subnet.id
  }

  vpc  = ibm_is_vpc.vpc.id
  zone = var.ibm_zone
  keys = [data.ibm_is_ssh_key.ssh_key.id]
}##############################################################################
# Virtual Server Instance: 
# Migrated from VMware via RVTools
##############################################################################

resource "ibm_is_instance" "isim1-prod-va-hicloud-orgin" {
  name    = "isim1-prod-va-hicloud-orgin"
  image   = var.image_id
  profile = "bx2-4x16"

  primary_network_interface {
    subnet = ibm_is_subnet.subnet.id
  }

  vpc  = ibm_is_vpc.vpc.id
  zone = var.ibm_zone
  keys = [data.ibm_is_ssh_key.ssh_key.id]
}##############################################################################
# Virtual Server Instance: 
# Migrated from VMware via RVTools
##############################################################################

resource "ibm_is_instance" "isim1-stg-va-hicloud" {
  name    = "isim1-stg-va-hicloud"
  image   = var.image_id
  profile = "bx2-4x16"

  primary_network_interface {
    subnet = ibm_is_subnet.subnet.id
  }

  vpc  = ibm_is_vpc.vpc.id
  zone = var.ibm_zone
  keys = [data.ibm_is_ssh_key.ssh_key.id]
}##############################################################################
# Virtual Server Instance: 
# Migrated from VMware via RVTools
##############################################################################

resource "ibm_is_instance" "ispim-template" {
  name    = "ispim-template"
  image   = var.image_id
  profile = "cx2-2x4"

  primary_network_interface {
    subnet = ibm_is_subnet.subnet.id
  }

  vpc  = ibm_is_vpc.vpc.id
  zone = var.ibm_zone
  keys = [data.ibm_is_ssh_key.ssh_key.id]
}##############################################################################
# Virtual Server Instance: 
# Migrated from VMware via RVTools
##############################################################################

resource "ibm_is_instance" "ispim-prod-va-hicloud-orgin" {
  name    = "ispim-prod-va-hicloud-orgin"
  image   = var.image_id
  profile = "cx2-2x4"

  primary_network_interface {
    subnet = ibm_is_subnet.subnet.id
  }

  vpc  = ibm_is_vpc.vpc.id
  zone = var.ibm_zone
  keys = [data.ibm_is_ssh_key.ssh_key.id]
}##############################################################################
# Virtual Server Instance: 
# Migrated from VMware via RVTools
##############################################################################

resource "ibm_is_instance" "isvd01-dev-va-hicloud" {
  name    = "isvd01-dev-va-hicloud"
  image   = var.image_id
  profile = "cx2-2x4"

  primary_network_interface {
    subnet = ibm_is_subnet.subnet.id
  }

  vpc  = ibm_is_vpc.vpc.id
  zone = var.ibm_zone
  keys = [data.ibm_is_ssh_key.ssh_key.id]
}##############################################################################
# Virtual Server Instance: 
# Migrated from VMware via RVTools
##############################################################################

resource "ibm_is_instance" "isvd01-prod-va-hicloud" {
  name    = "isvd01-prod-va-hicloud"
  image   = var.image_id
  profile = "bx2-2x8"

  primary_network_interface {
    subnet = ibm_is_subnet.subnet.id
  }

  vpc  = ibm_is_vpc.vpc.id
  zone = var.ibm_zone
  keys = [data.ibm_is_ssh_key.ssh_key.id]
}##############################################################################
# Virtual Server Instance: 
# Migrated from VMware via RVTools
##############################################################################

resource "ibm_is_instance" "isvd01-sit-va-hicloud" {
  name    = "isvd01-sit-va-hicloud"
  image   = var.image_id
  profile = "bx2-2x8"

  primary_network_interface {
    subnet = ibm_is_subnet.subnet.id
  }

  vpc  = ibm_is_vpc.vpc.id
  zone = var.ibm_zone
  keys = [data.ibm_is_ssh_key.ssh_key.id]
}##############################################################################
# Virtual Server Instance: 
# Migrated from VMware via RVTools
##############################################################################

resource "ibm_is_instance" "isvd01-stg-va-hicloud" {
  name    = "isvd01-stg-va-hicloud"
  image   = var.image_id
  profile = "bx2-2x8"

  primary_network_interface {
    subnet = ibm_is_subnet.subnet.id
  }

  vpc  = ibm_is_vpc.vpc.id
  zone = var.ibm_zone
  keys = [data.ibm_is_ssh_key.ssh_key.id]
}##############################################################################
# Virtual Server Instance: 
# Migrated from VMware via RVTools
##############################################################################

resource "ibm_is_instance" "isvd02-prod-va-hicloud" {
  name    = "isvd02-prod-va-hicloud"
  image   = var.image_id
  profile = "bx2-2x8"

  primary_network_interface {
    subnet = ibm_is_subnet.subnet.id
  }

  vpc  = ibm_is_vpc.vpc.id
  zone = var.ibm_zone
  keys = [data.ibm_is_ssh_key.ssh_key.id]
}##############################################################################
# Virtual Server Instance: 
# Migrated from VMware via RVTools
##############################################################################

resource "ibm_is_instance" "isvd02-stg-va-hicloud" {
  name    = "isvd02-stg-va-hicloud"
  image   = var.image_id
  profile = "bx2-2x8"

  primary_network_interface {
    subnet = ibm_is_subnet.subnet.id
  }

  vpc  = ibm_is_vpc.vpc.id
  zone = var.ibm_zone
  keys = [data.ibm_is_ssh_key.ssh_key.id]
}##############################################################################
# Virtual Server Instance: 
# Migrated from VMware via RVTools
##############################################################################

resource "ibm_is_instance" "jenkins-va-hicloud" {
  name    = "jenkins-va-hicloud"
  image   = var.image_id
  profile = "bx2-2x8"

  primary_network_interface {
    subnet = ibm_is_subnet.subnet.id
  }

  vpc  = ibm_is_vpc.vpc.id
  zone = var.ibm_zone
  keys = [data.ibm_is_ssh_key.ssh_key.id]
}##############################################################################
# Virtual Server Instance: 
# Migrated from VMware via RVTools
##############################################################################

resource "ibm_is_instance" "jira-va-hicloud" {
  name    = "jira-va-hicloud"
  image   = var.image_id
  profile = "bx2-2x10"

  primary_network_interface {
    subnet = ibm_is_subnet.subnet.id
  }

  vpc  = ibm_is_vpc.vpc.id
  zone = var.ibm_zone
  keys = [data.ibm_is_ssh_key.ssh_key.id]
}##############################################################################
# Virtual Server Instance: 
# Migrated from VMware via RVTools
##############################################################################

resource "ibm_is_instance" "moveit-auto-va-hicloud" {
  name    = "moveit-auto-va-hicloud"
  image   = var.image_id
  profile = "bx2-4x16"

  primary_network_interface {
    subnet = ibm_is_subnet.subnet.id
  }

  vpc  = ibm_is_vpc.vpc.id
  zone = var.ibm_zone
  keys = [data.ibm_is_ssh_key.ssh_key.id]
}##############################################################################
# Virtual Server Instance: 
# Migrated from VMware via RVTools
##############################################################################

resource "ibm_is_instance" "moveit-central-prod-va-hicloud" {
  name    = "moveit-central-prod-va-hicloud"
  image   = var.image_id
  profile = "bx2-4x16"

  primary_network_interface {
    subnet = ibm_is_subnet.subnet.id
  }

  vpc  = ibm_is_vpc.vpc.id
  zone = var.ibm_zone
  keys = [data.ibm_is_ssh_key.ssh_key.id]
}##############################################################################
# Virtual Server Instance: 
# Migrated from VMware via RVTools
##############################################################################

resource "ibm_is_instance" "moveit-central-prod-va-hicloud_standby" {
  name    = "moveit-central-prod-va-hicloud_standby"
  image   = var.image_id
  profile = "bx2-4x16"

  primary_network_interface {
    subnet = ibm_is_subnet.subnet.id
  }

  vpc  = ibm_is_vpc.vpc.id
  zone = var.ibm_zone
  keys = [data.ibm_is_ssh_key.ssh_key.id]
}##############################################################################
# Virtual Server Instance: 
# Migrated from VMware via RVTools
##############################################################################

resource "ibm_is_instance" "moveit-dmz-dmz-va-hicloud" {
  name    = "moveit-dmz-dmz-va-hicloud"
  image   = var.image_id
  profile = "bx2-4x16"

  primary_network_interface {
    subnet = ibm_is_subnet.subnet.id
  }

  vpc  = ibm_is_vpc.vpc.id
  zone = var.ibm_zone
  keys = [data.ibm_is_ssh_key.ssh_key.id]
}##############################################################################
# Virtual Server Instance: 
# Migrated from VMware via RVTools
##############################################################################

resource "ibm_is_instance" "moveit-mft-prod-va-hicloud" {
  name    = "moveit-mft-prod-va-hicloud"
  image   = var.image_id
  profile = "cx2-8x16"

  primary_network_interface {
    subnet = ibm_is_subnet.subnet.id
  }

  vpc  = ibm_is_vpc.vpc.id
  zone = var.ibm_zone
  keys = [data.ibm_is_ssh_key.ssh_key.id]
}##############################################################################
# Virtual Server Instance: 
# Migrated from VMware via RVTools
##############################################################################

resource "ibm_is_instance" "moveit-mft-prod-va-hicloud_standby" {
  name    = "moveit-mft-prod-va-hicloud_standby"
  image   = var.image_id
  profile = "cx2-8x16"

  primary_network_interface {
    subnet = ibm_is_subnet.subnet.id
  }

  vpc  = ibm_is_vpc.vpc.id
  zone = var.ibm_zone
  keys = [data.ibm_is_ssh_key.ssh_key.id]
}##############################################################################
# Virtual Server Instance: 
# Migrated from VMware via RVTools
##############################################################################

resource "ibm_is_instance" "mwg01-prod-va-hicloud" {
  name    = "mwg01-prod-va-hicloud"
  image   = var.image_id
  profile = "bx2-8x32"

  primary_network_interface {
    subnet = ibm_is_subnet.subnet.id
  }

  vpc  = ibm_is_vpc.vpc.id
  zone = var.ibm_zone
  keys = [data.ibm_is_ssh_key.ssh_key.id]
}##############################################################################
# Virtual Server Instance: 
# Migrated from VMware via RVTools
##############################################################################

resource "ibm_is_instance" "mwg02-prod-va-hicloud" {
  name    = "mwg02-prod-va-hicloud"
  image   = var.image_id
  profile = "bx2-8x32"

  primary_network_interface {
    subnet = ibm_is_subnet.subnet.id
  }

  vpc  = ibm_is_vpc.vpc.id
  zone = var.ibm_zone
  keys = [data.ibm_is_ssh_key.ssh_key.id]
}##############################################################################
# Virtual Server Instance: 
# Migrated from VMware via RVTools
##############################################################################

resource "ibm_is_instance" "mwg02-va-hicloud" {
  name    = "mwg02-va-hicloud"
  image   = var.image_id
  profile = "mx2-4x32"

  primary_network_interface {
    subnet = ibm_is_subnet.subnet.id
  }

  vpc  = ibm_is_vpc.vpc.id
  zone = var.ibm_zone
  keys = [data.ibm_is_ssh_key.ssh_key.id]
}##############################################################################
# Virtual Server Instance: 
# Migrated from VMware via RVTools
##############################################################################

resource "ibm_is_instance" "mysql-va-hicloud" {
  name    = "mysql-va-hicloud"
  image   = var.image_id
  profile = "cx2-2x4"

  primary_network_interface {
    subnet = ibm_is_subnet.subnet.id
  }

  vpc  = ibm_is_vpc.vpc.id
  zone = var.ibm_zone
  keys = [data.ibm_is_ssh_key.ssh_key.id]
}##############################################################################
# Virtual Server Instance: 
# Migrated from VMware via RVTools
##############################################################################

resource "ibm_is_instance" "prod01" {
  name    = "prod01"
  image   = var.image_id
  profile = "bx2-8x32"

  primary_network_interface {
    subnet = ibm_is_subnet.subnet.id
  }

  vpc  = ibm_is_vpc.vpc.id
  zone = var.ibm_zone
  keys = [data.ibm_is_ssh_key.ssh_key.id]
}##############################################################################
# Virtual Server Instance: 
# Migrated from VMware via RVTools
##############################################################################

resource "ibm_is_instance" "prod02" {
  name    = "prod02"
  image   = var.image_id
  profile = "bx2-8x32"

  primary_network_interface {
    subnet = ibm_is_subnet.subnet.id
  }

  vpc  = ibm_is_vpc.vpc.id
  zone = var.ibm_zone
  keys = [data.ibm_is_ssh_key.ssh_key.id]
}##############################################################################
# Virtual Server Instance: 
# Migrated from VMware via RVTools
##############################################################################

resource "ibm_is_instance" "rdl01-va-hicloud" {
  name    = "rdl01-va-hicloud"
  image   = var.image_id
  profile = "cx2-2x4"

  primary_network_interface {
    subnet = ibm_is_subnet.subnet.id
  }

  vpc  = ibm_is_vpc.vpc.id
  zone = var.ibm_zone
  keys = [data.ibm_is_ssh_key.ssh_key.id]
}##############################################################################
# Virtual Server Instance: 
# Migrated from VMware via RVTools
##############################################################################

resource "ibm_is_instance" "rhel8-template" {
  name    = "rhel8-template"
  image   = var.image_id
  profile = "cx2-2x2"

  primary_network_interface {
    subnet = ibm_is_subnet.subnet.id
  }

  vpc  = ibm_is_vpc.vpc.id
  zone = var.ibm_zone
  keys = [data.ibm_is_ssh_key.ssh_key.id]
}##############################################################################
# Virtual Server Instance: 
# Migrated from VMware via RVTools
##############################################################################

resource "ibm_is_instance" "rhel8-template-old" {
  name    = "rhel8-template-old"
  image   = var.image_id
  profile = "cx2-2x4"

  primary_network_interface {
    subnet = ibm_is_subnet.subnet.id
  }

  vpc  = ibm_is_vpc.vpc.id
  zone = var.ibm_zone
  keys = [data.ibm_is_ssh_key.ssh_key.id]
}##############################################################################
# Virtual Server Instance: 
# Migrated from VMware via RVTools
##############################################################################

resource "ibm_is_instance" "rhel-template" {
  name    = "rhel-template"
  image   = var.image_id
  profile = "cx2-2x4"

  primary_network_interface {
    subnet = ibm_is_subnet.subnet.id
  }

  vpc  = ibm_is_vpc.vpc.id
  zone = var.ibm_zone
  keys = [data.ibm_is_ssh_key.ssh_key.id]
}##############################################################################
# Virtual Server Instance: 
# Migrated from VMware via RVTools
##############################################################################

resource "ibm_is_instance" "sepm01-va-hicloud" {
  name    = "sepm01-va-hicloud"
  image   = var.image_id
  profile = "cx2-4x8"

  primary_network_interface {
    subnet = ibm_is_subnet.subnet.id
  }

  vpc  = ibm_is_vpc.vpc.id
  zone = var.ibm_zone
  keys = [data.ibm_is_ssh_key.ssh_key.id]
}##############################################################################
# Virtual Server Instance: 
# Migrated from VMware via RVTools
##############################################################################

resource "ibm_is_instance" "server2022gold1" {
  name    = "server2022gold1"
  image   = var.image_id
  profile = "cx2-2x4"

  primary_network_interface {
    subnet = ibm_is_subnet.subnet.id
  }

  vpc  = ibm_is_vpc.vpc.id
  zone = var.ibm_zone
  keys = [data.ibm_is_ssh_key.ssh_key.id]
}##############################################################################
# Virtual Server Instance: 
# Migrated from VMware via RVTools
##############################################################################

resource "ibm_is_instance" "servicenow-va-hicloud" {
  name    = "servicenow-va-hicloud"
  image   = var.image_id
  profile = "cx2-4x8"

  primary_network_interface {
    subnet = ibm_is_subnet.subnet.id
  }

  vpc  = ibm_is_vpc.vpc.id
  zone = var.ibm_zone
  keys = [data.ibm_is_ssh_key.ssh_key.id]
}##############################################################################
# Virtual Server Instance: 
# Migrated from VMware via RVTools
##############################################################################

resource "ibm_is_instance" "sftp01-va-hicloud" {
  name    = "sftp01-va-hicloud"
  image   = var.image_id
  profile = "cx2-2x4"

  primary_network_interface {
    subnet = ibm_is_subnet.subnet.id
  }

  vpc  = ibm_is_vpc.vpc.id
  zone = var.ibm_zone
  keys = [data.ibm_is_ssh_key.ssh_key.id]
}##############################################################################
# Virtual Server Instance: 
# Migrated from VMware via RVTools
##############################################################################

resource "ibm_is_instance" "sgw-va-1-2-1-0-24042317_ovf10" {
  name    = "sgw-va-1-2-1-0-24042317_ovf10"
  image   = var.image_id
  profile = "cx2-8x8"

  primary_network_interface {
    subnet = ibm_is_subnet.subnet.id
  }

  vpc  = ibm_is_vpc.vpc.id
  zone = var.ibm_zone
  keys = [data.ibm_is_ssh_key.ssh_key.id]
}##############################################################################
# Virtual Server Instance: 
# Migrated from VMware via RVTools
##############################################################################

resource "ibm_is_instance" "sit01" {
  name    = "sit01"
  image   = var.image_id
  profile = "cx2-4x8"

  primary_network_interface {
    subnet = ibm_is_subnet.subnet.id
  }

  vpc  = ibm_is_vpc.vpc.id
  zone = var.ibm_zone
  keys = [data.ibm_is_ssh_key.ssh_key.id]
}##############################################################################
# Virtual Server Instance: 
# Migrated from VMware via RVTools
##############################################################################

resource "ibm_is_instance" "sit02" {
  name    = "sit02"
  image   = var.image_id
  profile = "cx2-4x8"

  primary_network_interface {
    subnet = ibm_is_subnet.subnet.id
  }

  vpc  = ibm_is_vpc.vpc.id
  zone = var.ibm_zone
  keys = [data.ibm_is_ssh_key.ssh_key.id]
}##############################################################################
# Virtual Server Instance: 
# Migrated from VMware via RVTools
##############################################################################

resource "ibm_is_instance" "sklm02-bcr-va-healthinteractive-net" {
  name    = "sklm02-bcr-va-healthinteractive-net"
  image   = var.image_id
  profile = "bx2-4x16"

  primary_network_interface {
    subnet = ibm_is_subnet.subnet.id
  }

  vpc  = ibm_is_vpc.vpc.id
  zone = var.ibm_zone
  keys = [data.ibm_is_ssh_key.ssh_key.id]
}##############################################################################
# Virtual Server Instance: 
# Migrated from VMware via RVTools
##############################################################################

resource "ibm_is_instance" "sklm03-bcr-va-healthinteractive-net" {
  name    = "sklm03-bcr-va-healthinteractive-net"
  image   = var.image_id
  profile = "bx2-4x16"

  primary_network_interface {
    subnet = ibm_is_subnet.subnet.id
  }

  vpc  = ibm_is_vpc.vpc.id
  zone = var.ibm_zone
  keys = [data.ibm_is_ssh_key.ssh_key.id]
}##############################################################################
# Virtual Server Instance: 
# Migrated from VMware via RVTools
##############################################################################

resource "ibm_is_instance" "splunk-va-hicloud" {
  name    = "splunk-va-hicloud"
  image   = var.image_id
  profile = "cx2-16x24"

  primary_network_interface {
    subnet = ibm_is_subnet.subnet.id
  }

  vpc  = ibm_is_vpc.vpc.id
  zone = var.ibm_zone
  keys = [data.ibm_is_ssh_key.ssh_key.id]
}##############################################################################
# Virtual Server Instance: 
# Migrated from VMware via RVTools
##############################################################################

resource "ibm_is_instance" "splunkdeployment-va-hicloud" {
  name    = "splunkdeployment-va-hicloud"
  image   = var.image_id
  profile = "cx2-4x8"

  primary_network_interface {
    subnet = ibm_is_subnet.subnet.id
  }

  vpc  = ibm_is_vpc.vpc.id
  zone = var.ibm_zone
  keys = [data.ibm_is_ssh_key.ssh_key.id]
}##############################################################################
# Virtual Server Instance: 
# Migrated from VMware via RVTools
##############################################################################

resource "ibm_is_instance" "splunkdevdeployment-va-hicloud" {
  name    = "splunkdevdeployment-va-hicloud"
  image   = var.image_id
  profile = "cx2-4x8"

  primary_network_interface {
    subnet = ibm_is_subnet.subnet.id
  }

  vpc  = ibm_is_vpc.vpc.id
  zone = var.ibm_zone
  keys = [data.ibm_is_ssh_key.ssh_key.id]
}##############################################################################
# Virtual Server Instance: 
# Migrated from VMware via RVTools
##############################################################################

resource "ibm_is_instance" "splunkdevhf-va-hicloud" {
  name    = "splunkdevhf-va-hicloud"
  image   = var.image_id
  profile = "cx2-4x8"

  primary_network_interface {
    subnet = ibm_is_subnet.subnet.id
  }

  vpc  = ibm_is_vpc.vpc.id
  zone = var.ibm_zone
  keys = [data.ibm_is_ssh_key.ssh_key.id]
}##############################################################################
# Virtual Server Instance: 
# Migrated from VMware via RVTools
##############################################################################

resource "ibm_is_instance" "splunkdevindexer1-va-hicloud" {
  name    = "splunkdevindexer1-va-hicloud"
  image   = var.image_id
  profile = "cx2-16x24"

  primary_network_interface {
    subnet = ibm_is_subnet.subnet.id
  }

  vpc  = ibm_is_vpc.vpc.id
  zone = var.ibm_zone
  keys = [data.ibm_is_ssh_key.ssh_key.id]
}##############################################################################
# Virtual Server Instance: 
# Migrated from VMware via RVTools
##############################################################################

resource "ibm_is_instance" "splunkes-va-hicloud" {
  name    = "splunkes-va-hicloud"
  image   = var.image_id
  profile = "cx2-16x24"

  primary_network_interface {
    subnet = ibm_is_subnet.subnet.id
  }

  vpc  = ibm_is_vpc.vpc.id
  zone = var.ibm_zone
  keys = [data.ibm_is_ssh_key.ssh_key.id]
}##############################################################################
# Virtual Server Instance: 
# Migrated from VMware via RVTools
##############################################################################

resource "ibm_is_instance" "splunkhf-va-hicloud" {
  name    = "splunkhf-va-hicloud"
  image   = var.image_id
  profile = "cx2-6x7"

  primary_network_interface {
    subnet = ibm_is_subnet.subnet.id
  }

  vpc  = ibm_is_vpc.vpc.id
  zone = var.ibm_zone
  keys = [data.ibm_is_ssh_key.ssh_key.id]
}##############################################################################
# Virtual Server Instance: 
# Migrated from VMware via RVTools
##############################################################################

resource "ibm_is_instance" "splunkindexer1-va-hicloud" {
  name    = "splunkindexer1-va-hicloud"
  image   = var.image_id
  profile = "cx2-16x24"

  primary_network_interface {
    subnet = ibm_is_subnet.subnet.id
  }

  vpc  = ibm_is_vpc.vpc.id
  zone = var.ibm_zone
  keys = [data.ibm_is_ssh_key.ssh_key.id]
}##############################################################################
# Virtual Server Instance: 
# Migrated from VMware via RVTools
##############################################################################

resource "ibm_is_instance" "splunkindexer2-va-hicloud" {
  name    = "splunkindexer2-va-hicloud"
  image   = var.image_id
  profile = "cx2-16x24"

  primary_network_interface {
    subnet = ibm_is_subnet.subnet.id
  }

  vpc  = ibm_is_vpc.vpc.id
  zone = var.ibm_zone
  keys = [data.ibm_is_ssh_key.ssh_key.id]
}##############################################################################
# Virtual Server Instance: 
# Migrated from VMware via RVTools
##############################################################################

resource "ibm_is_instance" "splunkindexmaster-va-hicloud" {
  name    = "splunkindexmaster-va-hicloud"
  image   = var.image_id
  profile = "cx2-4x8"

  primary_network_interface {
    subnet = ibm_is_subnet.subnet.id
  }

  vpc  = ibm_is_vpc.vpc.id
  zone = var.ibm_zone
  keys = [data.ibm_is_ssh_key.ssh_key.id]
}##############################################################################
# Virtual Server Instance: 
# Migrated from VMware via RVTools
##############################################################################

resource "ibm_is_instance" "splunklicensemaster-va-hicloud" {
  name    = "splunklicensemaster-va-hicloud"
  image   = var.image_id
  profile = "cx2-2x4"

  primary_network_interface {
    subnet = ibm_is_subnet.subnet.id
  }

  vpc  = ibm_is_vpc.vpc.id
  zone = var.ibm_zone
  keys = [data.ibm_is_ssh_key.ssh_key.id]
}##############################################################################
# Virtual Server Instance: 
# Migrated from VMware via RVTools
##############################################################################

resource "ibm_is_instance" "sspr-va-hicloud" {
  name    = "sspr-va-hicloud"
  image   = var.image_id
  profile = "cx2-2x4"

  primary_network_interface {
    subnet = ibm_is_subnet.subnet.id
  }

  vpc  = ibm_is_vpc.vpc.id
  zone = var.ibm_zone
  keys = [data.ibm_is_ssh_key.ssh_key.id]
}##############################################################################
# Virtual Server Instance: 
# Migrated from VMware via RVTools
##############################################################################

resource "ibm_is_instance" "sspr02-va-hicloud" {
  name    = "sspr02-va-hicloud"
  image   = var.image_id
  profile = "cx2-2x4"

  primary_network_interface {
    subnet = ibm_is_subnet.subnet.id
  }

  vpc  = ibm_is_vpc.vpc.id
  zone = var.ibm_zone
  keys = [data.ibm_is_ssh_key.ssh_key.id]
}##############################################################################
# Virtual Server Instance: 
# Migrated from VMware via RVTools
##############################################################################

resource "ibm_is_instance" "stg01" {
  name    = "stg01"
  image   = var.image_id
  profile = "bx2-8x32"

  primary_network_interface {
    subnet = ibm_is_subnet.subnet.id
  }

  vpc  = ibm_is_vpc.vpc.id
  zone = var.ibm_zone
  keys = [data.ibm_is_ssh_key.ssh_key.id]
}##############################################################################
# Virtual Server Instance: 
# Migrated from VMware via RVTools
##############################################################################

resource "ibm_is_instance" "stg02" {
  name    = "stg02"
  image   = var.image_id
  profile = "bx2-8x32"

  primary_network_interface {
    subnet = ibm_is_subnet.subnet.id
  }

  vpc  = ibm_is_vpc.vpc.id
  zone = var.ibm_zone
  keys = [data.ibm_is_ssh_key.ssh_key.id]
}##############################################################################
# Virtual Server Instance: 
# Migrated from VMware via RVTools
##############################################################################

resource "ibm_is_instance" "symantec-2-va-hicloud" {
  name    = "symantec-2-va-hicloud"
  image   = var.image_id
  profile = "cx2-16x16"

  primary_network_interface {
    subnet = ibm_is_subnet.subnet.id
  }

  vpc  = ibm_is_vpc.vpc.id
  zone = var.ibm_zone
  keys = [data.ibm_is_ssh_key.ssh_key.id]
}##############################################################################
# Virtual Server Instance: 
# Migrated from VMware via RVTools
##############################################################################

resource "ibm_is_instance" "symc1-prod-va-hicloud" {
  name    = "symc1-prod-va-hicloud"
  image   = var.image_id
  profile = "bx2-4x30"

  primary_network_interface {
    subnet = ibm_is_subnet.subnet.id
  }

  vpc  = ibm_is_vpc.vpc.id
  zone = var.ibm_zone
  keys = [data.ibm_is_ssh_key.ssh_key.id]
}##############################################################################
# Virtual Server Instance: 
# Migrated from VMware via RVTools
##############################################################################

resource "ibm_is_instance" "va-jira-mysql-dep" {
  name    = "va-jira-mysql-dep"
  image   = var.image_id
  profile = "cx2-2x4"

  primary_network_interface {
    subnet = ibm_is_subnet.subnet.id
  }

  vpc  = ibm_is_vpc.vpc.id
  zone = var.ibm_zone
  keys = [data.ibm_is_ssh_key.ssh_key.id]
}##############################################################################
# Virtual Server Instance: 
# Migrated from VMware via RVTools
##############################################################################

resource "ibm_is_instance" "vapldace01-dev-va-hicloud" {
  name    = "vapldace01-dev-va-hicloud"
  image   = var.image_id
  profile = "mx2-2x24"

  primary_network_interface {
    subnet = ibm_is_subnet.subnet.id
  }

  vpc  = ibm_is_vpc.vpc.id
  zone = var.ibm_zone
  keys = [data.ibm_is_ssh_key.ssh_key.id]
}##############################################################################
# Virtual Server Instance: 
# Migrated from VMware via RVTools
##############################################################################

resource "ibm_is_instance" "vapldcsvn01-dev-va-hicloud" {
  name    = "vapldcsvn01-dev-va-hicloud"
  image   = var.image_id
  profile = "cx2-2x4"

  primary_network_interface {
    subnet = ibm_is_subnet.subnet.id
  }

  vpc  = ibm_is_vpc.vpc.id
  zone = var.ibm_zone
  keys = [data.ibm_is_ssh_key.ssh_key.id]
}##############################################################################
# Virtual Server Instance: 
# Migrated from VMware via RVTools
##############################################################################

resource "ibm_is_instance" "vapldibmdb01-dev-va-hicloud" {
  name    = "vapldibmdb01-dev-va-hicloud"
  image   = var.image_id
  profile = "bx2-4x16"

  primary_network_interface {
    subnet = ibm_is_subnet.subnet.id
  }

  vpc  = ibm_is_vpc.vpc.id
  zone = var.ibm_zone
  keys = [data.ibm_is_ssh_key.ssh_key.id]
}##############################################################################
# Virtual Server Instance: 
# Migrated from VMware via RVTools
##############################################################################

resource "ibm_is_instance" "vapldlbas01-dev-va-hicloud" {
  name    = "vapldlbas01-dev-va-hicloud"
  image   = var.image_id
  profile = "cx2-2x4"

  primary_network_interface {
    subnet = ibm_is_subnet.subnet.id
  }

  vpc  = ibm_is_vpc.vpc.id
  zone = var.ibm_zone
  keys = [data.ibm_is_ssh_key.ssh_key.id]
}##############################################################################
# Virtual Server Instance: 
# Migrated from VMware via RVTools
##############################################################################

resource "ibm_is_instance" "vapldmq01-dev-va-hicloud" {
  name    = "vapldmq01-dev-va-hicloud"
  image   = var.image_id
  profile = "bx2-4x12"

  primary_network_interface {
    subnet = ibm_is_subnet.subnet.id
  }

  vpc  = ibm_is_vpc.vpc.id
  zone = var.ibm_zone
  keys = [data.ibm_is_ssh_key.ssh_key.id]
}##############################################################################
# Virtual Server Instance: 
# Migrated from VMware via RVTools
##############################################################################

resource "ibm_is_instance" "vapldmqp01-dev-va-hicloud" {
  name    = "vapldmqp01-dev-va-hicloud"
  image   = var.image_id
  profile = "mx2-1x8"

  primary_network_interface {
    subnet = ibm_is_subnet.subnet.id
  }

  vpc  = ibm_is_vpc.vpc.id
  zone = var.ibm_zone
  keys = [data.ibm_is_ssh_key.ssh_key.id]
}##############################################################################
# Virtual Server Instance: 
# Migrated from VMware via RVTools
##############################################################################

resource "ibm_is_instance" "vapldport01-dev-va-hicloud" {
  name    = "vapldport01-dev-va-hicloud"
  image   = var.image_id
  profile = "bx2-2x8"

  primary_network_interface {
    subnet = ibm_is_subnet.subnet.id
  }

  vpc  = ibm_is_vpc.vpc.id
  zone = var.ibm_zone
  keys = [data.ibm_is_ssh_key.ssh_key.id]
}##############################################################################
# Virtual Server Instance: 
# Migrated from VMware via RVTools
##############################################################################

resource "ibm_is_instance" "vapldwas01-dev-va-hicloud" {
  name    = "vapldwas01-dev-va-hicloud"
  image   = var.image_id
  profile = "bx2-2x8"

  primary_network_interface {
    subnet = ibm_is_subnet.subnet.id
  }

  vpc  = ibm_is_vpc.vpc.id
  zone = var.ibm_zone
  keys = [data.ibm_is_ssh_key.ssh_key.id]
}##############################################################################
# Virtual Server Instance: 
# Migrated from VMware via RVTools
##############################################################################

resource "ibm_is_instance" "vapldwsrr01-dev-va-hicloud" {
  name    = "vapldwsrr01-dev-va-hicloud"
  image   = var.image_id
  profile = "cx2-4x8"

  primary_network_interface {
    subnet = ibm_is_subnet.subnet.id
  }

  vpc  = ibm_is_vpc.vpc.id
  zone = var.ibm_zone
  keys = [data.ibm_is_ssh_key.ssh_key.id]
}##############################################################################
# Virtual Server Instance: 
# Migrated from VMware via RVTools
##############################################################################

resource "ibm_is_instance" "vaplnspdep11-va-hicloud" {
  name    = "vaplnspdep11-va-hicloud"
  image   = var.image_id
  profile = "cx2-4x8"

  primary_network_interface {
    subnet = ibm_is_subnet.subnet.id
  }

  vpc  = ibm_is_vpc.vpc.id
  zone = var.ibm_zone
  keys = [data.ibm_is_ssh_key.ssh_key.id]
}##############################################################################
# Virtual Server Instance: 
# Migrated from VMware via RVTools
##############################################################################

resource "ibm_is_instance" "vaplnsphf11-va-hicloud" {
  name    = "vaplnsphf11-va-hicloud"
  image   = var.image_id
  profile = "cx2-4x8"

  primary_network_interface {
    subnet = ibm_is_subnet.subnet.id
  }

  vpc  = ibm_is_vpc.vpc.id
  zone = var.ibm_zone
  keys = [data.ibm_is_ssh_key.ssh_key.id]
}##############################################################################
# Virtual Server Instance: 
# Migrated from VMware via RVTools
##############################################################################

resource "ibm_is_instance" "vaplnspin11-va-hicloud" {
  name    = "vaplnspin11-va-hicloud"
  image   = var.image_id
  profile = "cx2-8x16"

  primary_network_interface {
    subnet = ibm_is_subnet.subnet.id
  }

  vpc  = ibm_is_vpc.vpc.id
  zone = var.ibm_zone
  keys = [data.ibm_is_ssh_key.ssh_key.id]
}##############################################################################
# Virtual Server Instance: 
# Migrated from VMware via RVTools
##############################################################################

resource "ibm_is_instance" "vaplpace01-prod-va-hicloud" {
  name    = "vaplpace01-prod-va-hicloud"
  image   = var.image_id
  profile = "mx2-2x24"

  primary_network_interface {
    subnet = ibm_is_subnet.subnet.id
  }

  vpc  = ibm_is_vpc.vpc.id
  zone = var.ibm_zone
  keys = [data.ibm_is_ssh_key.ssh_key.id]
}##############################################################################
# Virtual Server Instance: 
# Migrated from VMware via RVTools
##############################################################################

resource "ibm_is_instance" "vaplpace02-prod-va-hicloud" {
  name    = "vaplpace02-prod-va-hicloud"
  image   = var.image_id
  profile = "mx2-2x24"

  primary_network_interface {
    subnet = ibm_is_subnet.subnet.id
  }

  vpc  = ibm_is_vpc.vpc.id
  zone = var.ibm_zone
  keys = [data.ibm_is_ssh_key.ssh_key.id]
}##############################################################################
# Virtual Server Instance: 
# Migrated from VMware via RVTools
##############################################################################

resource "ibm_is_instance" "vaplparch01-va-hicloud" {
  name    = "vaplparch01-va-hicloud"
  image   = var.image_id
  profile = "cx2-2x2"

  primary_network_interface {
    subnet = ibm_is_subnet.subnet.id
  }

  vpc  = ibm_is_vpc.vpc.id
  zone = var.ibm_zone
  keys = [data.ibm_is_ssh_key.ssh_key.id]
}##############################################################################
# Virtual Server Instance: 
# Migrated from VMware via RVTools
##############################################################################

resource "ibm_is_instance" "vaplpcms01-prod-va-hicloud" {
  name    = "vaplpcms01-prod-va-hicloud"
  image   = var.image_id
  profile = "cx2-2x4"

  primary_network_interface {
    subnet = ibm_is_subnet.subnet.id
  }

  vpc  = ibm_is_vpc.vpc.id
  zone = var.ibm_zone
  keys = [data.ibm_is_ssh_key.ssh_key.id]
}##############################################################################
# Virtual Server Instance: 
# Migrated from VMware via RVTools
##############################################################################

resource "ibm_is_instance" "vaplpcms02-prod-va-hicloud" {
  name    = "vaplpcms02-prod-va-hicloud"
  image   = var.image_id
  profile = "cx2-2x4"

  primary_network_interface {
    subnet = ibm_is_subnet.subnet.id
  }

  vpc  = ibm_is_vpc.vpc.id
  zone = var.ibm_zone
  keys = [data.ibm_is_ssh_key.ssh_key.id]
}##############################################################################
# Virtual Server Instance: 
# Migrated from VMware via RVTools
##############################################################################

resource "ibm_is_instance" "vaplpdns01-va-hicloud" {
  name    = "vaplpdns01-va-hicloud"
  image   = var.image_id
  profile = "cx2-2x4"

  primary_network_interface {
    subnet = ibm_is_subnet.subnet.id
  }

  vpc  = ibm_is_vpc.vpc.id
  zone = var.ibm_zone
  keys = [data.ibm_is_ssh_key.ssh_key.id]
}##############################################################################
# Virtual Server Instance: 
# Migrated from VMware via RVTools
##############################################################################

resource "ibm_is_instance" "vaplpdns02-va-hicloud" {
  name    = "vaplpdns02-va-hicloud"
  image   = var.image_id
  profile = "cx2-2x4"

  primary_network_interface {
    subnet = ibm_is_subnet.subnet.id
  }

  vpc  = ibm_is_vpc.vpc.id
  zone = var.ibm_zone
  keys = [data.ibm_is_ssh_key.ssh_key.id]
}##############################################################################
# Virtual Server Instance: 
# Migrated from VMware via RVTools
##############################################################################

resource "ibm_is_instance" "vaplpduo01-core-va-hicloud" {
  name    = "vaplpduo01-core-va-hicloud"
  image   = var.image_id
  profile = "cx2-2x4"

  primary_network_interface {
    subnet = ibm_is_subnet.subnet.id
  }

  vpc  = ibm_is_vpc.vpc.id
  zone = var.ibm_zone
  keys = [data.ibm_is_ssh_key.ssh_key.id]
}##############################################################################
# Virtual Server Instance: 
# Migrated from VMware via RVTools
##############################################################################

resource "ibm_is_instance" "vaplpibmdb01-prod-va-hicloud" {
  name    = "vaplpibmdb01-prod-va-hicloud"
  image   = var.image_id
  profile = "bx2-4x24"

  primary_network_interface {
    subnet = ibm_is_subnet.subnet.id
  }

  vpc  = ibm_is_vpc.vpc.id
  zone = var.ibm_zone
  keys = [data.ibm_is_ssh_key.ssh_key.id]
}##############################################################################
# Virtual Server Instance: 
# Migrated from VMware via RVTools
##############################################################################

resource "ibm_is_instance" "vaplpibmdb02-prod-va-hicloud" {
  name    = "vaplpibmdb02-prod-va-hicloud"
  image   = var.image_id
  profile = "bx2-4x24"

  primary_network_interface {
    subnet = ibm_is_subnet.subnet.id
  }

  vpc  = ibm_is_vpc.vpc.id
  zone = var.ibm_zone
  keys = [data.ibm_is_ssh_key.ssh_key.id]
}##############################################################################
# Virtual Server Instance: 
# Migrated from VMware via RVTools
##############################################################################

resource "ibm_is_instance" "vaplpibmdb21-prod-va-hicloud" {
  name    = "vaplpibmdb21-prod-va-hicloud"
  image   = var.image_id
  profile = "bx2-4x24"

  primary_network_interface {
    subnet = ibm_is_subnet.subnet.id
  }

  vpc  = ibm_is_vpc.vpc.id
  zone = var.ibm_zone
  keys = [data.ibm_is_ssh_key.ssh_key.id]
}##############################################################################
# Virtual Server Instance: 
# Migrated from VMware via RVTools
##############################################################################

resource "ibm_is_instance" "vaplpibmdb22-prod-va-hicloud" {
  name    = "vaplpibmdb22-prod-va-hicloud"
  image   = var.image_id
  profile = "bx2-4x24"

  primary_network_interface {
    subnet = ibm_is_subnet.subnet.id
  }

  vpc  = ibm_is_vpc.vpc.id
  zone = var.ibm_zone
  keys = [data.ibm_is_ssh_key.ssh_key.id]
}##############################################################################
# Virtual Server Instance: 
# Migrated from VMware via RVTools
##############################################################################

resource "ibm_is_instance" "vaplpjen01-core-va-hicloud" {
  name    = "vaplpjen01-core-va-hicloud"
  image   = var.image_id
  profile = "cx2-4x8"

  primary_network_interface {
    subnet = ibm_is_subnet.subnet.id
  }

  vpc  = ibm_is_vpc.vpc.id
  zone = var.ibm_zone
  keys = [data.ibm_is_ssh_key.ssh_key.id]
}##############################################################################
# Virtual Server Instance: 
# Migrated from VMware via RVTools
##############################################################################

resource "ibm_is_instance" "vaplpjen01-core-va-hicloud_bad_tbd_2025-09-17" {
  name    = "vaplpjen01-core-va-hicloud_bad_tbd_2025-09-17"
  image   = var.image_id
  profile = "cx2-4x8"

  primary_network_interface {
    subnet = ibm_is_subnet.subnet.id
  }

  vpc  = ibm_is_vpc.vpc.id
  zone = var.ibm_zone
  keys = [data.ibm_is_ssh_key.ssh_key.id]
}##############################################################################
# Virtual Server Instance: 
# Migrated from VMware via RVTools
##############################################################################

resource "ibm_is_instance" "vaplpjira01-core-va-hicloud" {
  name    = "vaplpjira01-core-va-hicloud"
  image   = var.image_id
  profile = "bx2-2x10"

  primary_network_interface {
    subnet = ibm_is_subnet.subnet.id
  }

  vpc  = ibm_is_vpc.vpc.id
  zone = var.ibm_zone
  keys = [data.ibm_is_ssh_key.ssh_key.id]
}##############################################################################
# Virtual Server Instance: 
# Migrated from VMware via RVTools
##############################################################################

resource "ibm_is_instance" "vaplplbas01-va-hicloud" {
  name    = "vaplplbas01-va-hicloud"
  image   = var.image_id
  profile = "cx2-2x4"

  primary_network_interface {
    subnet = ibm_is_subnet.subnet.id
  }

  vpc  = ibm_is_vpc.vpc.id
  zone = var.ibm_zone
  keys = [data.ibm_is_ssh_key.ssh_key.id]
}##############################################################################
# Virtual Server Instance: 
# Migrated from VMware via RVTools
##############################################################################

resource "ibm_is_instance" "vaplpmpage01-prod-va-hicloud_don't-delete" {
  name    = "vaplpmpage01-prod-va-hicloud_don't-delete"
  image   = var.image_id
  profile = "cx2-2x4"

  primary_network_interface {
    subnet = ibm_is_subnet.subnet.id
  }

  vpc  = ibm_is_vpc.vpc.id
  zone = var.ibm_zone
  keys = [data.ibm_is_ssh_key.ssh_key.id]
}##############################################################################
# Virtual Server Instance: 
# Migrated from VMware via RVTools
##############################################################################

resource "ibm_is_instance" "vaplpmq01-prod-va-hicloud" {
  name    = "vaplpmq01-prod-va-hicloud"
  image   = var.image_id
  profile = "cx2-4x8"

  primary_network_interface {
    subnet = ibm_is_subnet.subnet.id
  }

  vpc  = ibm_is_vpc.vpc.id
  zone = var.ibm_zone
  keys = [data.ibm_is_ssh_key.ssh_key.id]
}##############################################################################
# Virtual Server Instance: 
# Migrated from VMware via RVTools
##############################################################################

resource "ibm_is_instance" "vaplpmq02-prod-va-hicloud" {
  name    = "vaplpmq02-prod-va-hicloud"
  image   = var.image_id
  profile = "cx2-4x8"

  primary_network_interface {
    subnet = ibm_is_subnet.subnet.id
  }

  vpc  = ibm_is_vpc.vpc.id
  zone = var.ibm_zone
  keys = [data.ibm_is_ssh_key.ssh_key.id]
}##############################################################################
# Virtual Server Instance: 
# Migrated from VMware via RVTools
##############################################################################

resource "ibm_is_instance" "vaplpmqp01-prod-va-hicloud" {
  name    = "vaplpmqp01-prod-va-hicloud"
  image   = var.image_id
  profile = "cx2-4x8"

  primary_network_interface {
    subnet = ibm_is_subnet.subnet.id
  }

  vpc  = ibm_is_vpc.vpc.id
  zone = var.ibm_zone
  keys = [data.ibm_is_ssh_key.ssh_key.id]
}##############################################################################
# Virtual Server Instance: 
# Migrated from VMware via RVTools
##############################################################################

resource "ibm_is_instance" "vaplpmqp02-prod-va-hicloud" {
  name    = "vaplpmqp02-prod-va-hicloud"
  image   = var.image_id
  profile = "cx2-4x8"

  primary_network_interface {
    subnet = ibm_is_subnet.subnet.id
  }

  vpc  = ibm_is_vpc.vpc.id
  zone = var.ibm_zone
  keys = [data.ibm_is_ssh_key.ssh_key.id]
}##############################################################################
# Virtual Server Instance: 
# Migrated from VMware via RVTools
##############################################################################

resource "ibm_is_instance" "vaplpmysql01-core-va-hicloud" {
  name    = "vaplpmysql01-core-va-hicloud"
  image   = var.image_id
  profile = "cx2-2x4"

  primary_network_interface {
    subnet = ibm_is_subnet.subnet.id
  }

  vpc  = ibm_is_vpc.vpc.id
  zone = var.ibm_zone
  keys = [data.ibm_is_ssh_key.ssh_key.id]
}##############################################################################
# Virtual Server Instance: 
# Migrated from VMware via RVTools
##############################################################################

resource "ibm_is_instance" "vaplpnagios01-va-hicloud" {
  name    = "vaplpnagios01-va-hicloud"
  image   = var.image_id
  profile = "cx2-6x8"

  primary_network_interface {
    subnet = ibm_is_subnet.subnet.id
  }

  vpc  = ibm_is_vpc.vpc.id
  zone = var.ibm_zone
  keys = [data.ibm_is_ssh_key.ssh_key.id]
}##############################################################################
# Virtual Server Instance: 
# Migrated from VMware via RVTools
##############################################################################

resource "ibm_is_instance" "vaplpnas01-va-hicloud" {
  name    = "vaplpnas01-va-hicloud"
  image   = var.image_id
  profile = "cx2-2x2"

  primary_network_interface {
    subnet = ibm_is_subnet.subnet.id
  }

  vpc  = ibm_is_vpc.vpc.id
  zone = var.ibm_zone
  keys = [data.ibm_is_ssh_key.ssh_key.id]
}##############################################################################
# Virtual Server Instance: 
# Migrated from VMware via RVTools
##############################################################################

resource "ibm_is_instance" "vaplpntpsrv01-va-hicloud" {
  name    = "vaplpntpsrv01-va-hicloud"
  image   = var.image_id
  profile = "cx2-2x4"

  primary_network_interface {
    subnet = ibm_is_subnet.subnet.id
  }

  vpc  = ibm_is_vpc.vpc.id
  zone = var.ibm_zone
  keys = [data.ibm_is_ssh_key.ssh_key.id]
}##############################################################################
# Virtual Server Instance: 
# Migrated from VMware via RVTools
##############################################################################

resource "ibm_is_instance" "vaplprhrepo01-va-hicloud" {
  name    = "vaplprhrepo01-va-hicloud"
  image   = var.image_id
  profile = "cx2-2x4"

  primary_network_interface {
    subnet = ibm_is_subnet.subnet.id
  }

  vpc  = ibm_is_vpc.vpc.id
  zone = var.ibm_zone
  keys = [data.ibm_is_ssh_key.ssh_key.id]
}##############################################################################
# Virtual Server Instance: 
# Migrated from VMware via RVTools
##############################################################################

resource "ibm_is_instance" "vaplpslog01-va-hicloud" {
  name    = "vaplpslog01-va-hicloud"
  image   = var.image_id
  profile = "cx2-2x4"

  primary_network_interface {
    subnet = ibm_is_subnet.subnet.id
  }

  vpc  = ibm_is_vpc.vpc.id
  zone = var.ibm_zone
  keys = [data.ibm_is_ssh_key.ssh_key.id]
}##############################################################################
# Virtual Server Instance: 
# Migrated from VMware via RVTools
##############################################################################

resource "ibm_is_instance" "vaplpsmtp01-va-hicloud" {
  name    = "vaplpsmtp01-va-hicloud"
  image   = var.image_id
  profile = "cx2-2x4"

  primary_network_interface {
    subnet = ibm_is_subnet.subnet.id
  }

  vpc  = ibm_is_vpc.vpc.id
  zone = var.ibm_zone
  keys = [data.ibm_is_ssh_key.ssh_key.id]
}##############################################################################
# Virtual Server Instance: 
# Migrated from VMware via RVTools
##############################################################################

resource "ibm_is_instance" "vaplpsp01-va-hicloud" {
  name    = "vaplpsp01-va-hicloud"
  image   = var.image_id
  profile = "cx2-16x24"

  primary_network_interface {
    subnet = ibm_is_subnet.subnet.id
  }

  vpc  = ibm_is_vpc.vpc.id
  zone = var.ibm_zone
  keys = [data.ibm_is_ssh_key.ssh_key.id]
}##############################################################################
# Virtual Server Instance: 
# Migrated from VMware via RVTools
##############################################################################

resource "ibm_is_instance" "vaplpspdep01-va-hicloud" {
  name    = "vaplpspdep01-va-hicloud"
  image   = var.image_id
  profile = "cx2-4x8"

  primary_network_interface {
    subnet = ibm_is_subnet.subnet.id
  }

  vpc  = ibm_is_vpc.vpc.id
  zone = var.ibm_zone
  keys = [data.ibm_is_ssh_key.ssh_key.id]
}##############################################################################
# Virtual Server Instance: 
# Migrated from VMware via RVTools
##############################################################################

resource "ibm_is_instance" "vaplpspes01-va-hicloud" {
  name    = "vaplpspes01-va-hicloud"
  image   = var.image_id
  profile = "cx2-16x24"

  primary_network_interface {
    subnet = ibm_is_subnet.subnet.id
  }

  vpc  = ibm_is_vpc.vpc.id
  zone = var.ibm_zone
  keys = [data.ibm_is_ssh_key.ssh_key.id]
}##############################################################################
# Virtual Server Instance: 
# Migrated from VMware via RVTools
##############################################################################

resource "ibm_is_instance" "vaplpsphf01-va-hicloud" {
  name    = "vaplpsphf01-va-hicloud"
  image   = var.image_id
  profile = "cx2-6x8"

  primary_network_interface {
    subnet = ibm_is_subnet.subnet.id
  }

  vpc  = ibm_is_vpc.vpc.id
  zone = var.ibm_zone
  keys = [data.ibm_is_ssh_key.ssh_key.id]
}##############################################################################
# Virtual Server Instance: 
# Migrated from VMware via RVTools
##############################################################################

resource "ibm_is_instance" "vaplpspim01-va-hicloud" {
  name    = "vaplpspim01-va-hicloud"
  image   = var.image_id
  profile = "cx2-4x8"

  primary_network_interface {
    subnet = ibm_is_subnet.subnet.id
  }

  vpc  = ibm_is_vpc.vpc.id
  zone = var.ibm_zone
  keys = [data.ibm_is_ssh_key.ssh_key.id]
}##############################################################################
# Virtual Server Instance: 
# Migrated from VMware via RVTools
##############################################################################

resource "ibm_is_instance" "vaplpspin01-va-hicloud" {
  name    = "vaplpspin01-va-hicloud"
  image   = var.image_id
  profile = "cx2-16x24"

  primary_network_interface {
    subnet = ibm_is_subnet.subnet.id
  }

  vpc  = ibm_is_vpc.vpc.id
  zone = var.ibm_zone
  keys = [data.ibm_is_ssh_key.ssh_key.id]
}##############################################################################
# Virtual Server Instance: 
# Migrated from VMware via RVTools
##############################################################################

resource "ibm_is_instance" "vaplpspin02-va-hicloud" {
  name    = "vaplpspin02-va-hicloud"
  image   = var.image_id
  profile = "cx2-16x24"

  primary_network_interface {
    subnet = ibm_is_subnet.subnet.id
  }

  vpc  = ibm_is_vpc.vpc.id
  zone = var.ibm_zone
  keys = [data.ibm_is_ssh_key.ssh_key.id]
}##############################################################################
# Virtual Server Instance: 
# Migrated from VMware via RVTools
##############################################################################

resource "ibm_is_instance" "vaplpspxy01-va-hicloud" {
  name    = "vaplpspxy01-va-hicloud"
  image   = var.image_id
  profile = "cx2-2x4"

  primary_network_interface {
    subnet = ibm_is_subnet.subnet.id
  }

  vpc  = ibm_is_vpc.vpc.id
  zone = var.ibm_zone
  keys = [data.ibm_is_ssh_key.ssh_key.id]
}##############################################################################
# Virtual Server Instance: 
# Migrated from VMware via RVTools
##############################################################################

resource "ibm_is_instance" "vaplpurldir01-prod-va-hicloud" {
  name    = "vaplpurldir01-prod-va-hicloud"
  image   = var.image_id
  profile = "cx2-2x4"

  primary_network_interface {
    subnet = ibm_is_subnet.subnet.id
  }

  vpc  = ibm_is_vpc.vpc.id
  zone = var.ibm_zone
  keys = [data.ibm_is_ssh_key.ssh_key.id]
}##############################################################################
# Virtual Server Instance: 
# Migrated from VMware via RVTools
##############################################################################

resource "ibm_is_instance" "vaplpurldir02-prod-va-hicloud" {
  name    = "vaplpurldir02-prod-va-hicloud"
  image   = var.image_id
  profile = "cx2-2x4"

  primary_network_interface {
    subnet = ibm_is_subnet.subnet.id
  }

  vpc  = ibm_is_vpc.vpc.id
  zone = var.ibm_zone
  keys = [data.ibm_is_ssh_key.ssh_key.id]
}##############################################################################
# Virtual Server Instance: 
# Migrated from VMware via RVTools
##############################################################################

resource "ibm_is_instance" "vaplpwsrr01-prod-va-hicloud" {
  name    = "vaplpwsrr01-prod-va-hicloud"
  image   = var.image_id
  profile = "mx2-1x8"

  primary_network_interface {
    subnet = ibm_is_subnet.subnet.id
  }

  vpc  = ibm_is_vpc.vpc.id
  zone = var.ibm_zone
  keys = [data.ibm_is_ssh_key.ssh_key.id]
}##############################################################################
# Virtual Server Instance: 
# Migrated from VMware via RVTools
##############################################################################

resource "ibm_is_instance" "vaplpwsrr01-prod-va-hicloud_standby" {
  name    = "vaplpwsrr01-prod-va-hicloud_standby"
  image   = var.image_id
  profile = "mx2-1x8"

  primary_network_interface {
    subnet = ibm_is_subnet.subnet.id
  }

  vpc  = ibm_is_vpc.vpc.id
  zone = var.ibm_zone
  keys = [data.ibm_is_ssh_key.ssh_key.id]
}##############################################################################
# Virtual Server Instance: 
# Migrated from VMware via RVTools
##############################################################################

resource "ibm_is_instance" "vaplqace01-stg-va-hicloud" {
  name    = "vaplqace01-stg-va-hicloud"
  image   = var.image_id
  profile = "mx2-2x24"

  primary_network_interface {
    subnet = ibm_is_subnet.subnet.id
  }

  vpc  = ibm_is_vpc.vpc.id
  zone = var.ibm_zone
  keys = [data.ibm_is_ssh_key.ssh_key.id]
}##############################################################################
# Virtual Server Instance: 
# Migrated from VMware via RVTools
##############################################################################

resource "ibm_is_instance" "vaplqace02-stg-va-hicloud" {
  name    = "vaplqace02-stg-va-hicloud"
  image   = var.image_id
  profile = "mx2-2x24"

  primary_network_interface {
    subnet = ibm_is_subnet.subnet.id
  }

  vpc  = ibm_is_vpc.vpc.id
  zone = var.ibm_zone
  keys = [data.ibm_is_ssh_key.ssh_key.id]
}##############################################################################
# Virtual Server Instance: 
# Migrated from VMware via RVTools
##############################################################################

resource "ibm_is_instance" "vaplqcms01-stg-va-hicloud" {
  name    = "vaplqcms01-stg-va-hicloud"
  image   = var.image_id
  profile = "cx2-2x4"

  primary_network_interface {
    subnet = ibm_is_subnet.subnet.id
  }

  vpc  = ibm_is_vpc.vpc.id
  zone = var.ibm_zone
  keys = [data.ibm_is_ssh_key.ssh_key.id]
}##############################################################################
# Virtual Server Instance: 
# Migrated from VMware via RVTools
##############################################################################

resource "ibm_is_instance" "vaplqcms02-stg-va-hicloud" {
  name    = "vaplqcms02-stg-va-hicloud"
  image   = var.image_id
  profile = "cx2-2x4"

  primary_network_interface {
    subnet = ibm_is_subnet.subnet.id
  }

  vpc  = ibm_is_vpc.vpc.id
  zone = var.ibm_zone
  keys = [data.ibm_is_ssh_key.ssh_key.id]
}##############################################################################
# Virtual Server Instance: 
# Migrated from VMware via RVTools
##############################################################################

resource "ibm_is_instance" "vaplqibmdb01-stg-va-hicloud" {
  name    = "vaplqibmdb01-stg-va-hicloud"
  image   = var.image_id
  profile = "bx2-4x24"

  primary_network_interface {
    subnet = ibm_is_subnet.subnet.id
  }

  vpc  = ibm_is_vpc.vpc.id
  zone = var.ibm_zone
  keys = [data.ibm_is_ssh_key.ssh_key.id]
}##############################################################################
# Virtual Server Instance: 
# Migrated from VMware via RVTools
##############################################################################

resource "ibm_is_instance" "vaplqibmdb02-stg-va-hicloud" {
  name    = "vaplqibmdb02-stg-va-hicloud"
  image   = var.image_id
  profile = "bx2-4x24"

  primary_network_interface {
    subnet = ibm_is_subnet.subnet.id
  }

  vpc  = ibm_is_vpc.vpc.id
  zone = var.ibm_zone
  keys = [data.ibm_is_ssh_key.ssh_key.id]
}##############################################################################
# Virtual Server Instance: 
# Migrated from VMware via RVTools
##############################################################################

resource "ibm_is_instance" "vaplqibmdb21-stg-va-hicloud" {
  name    = "vaplqibmdb21-stg-va-hicloud"
  image   = var.image_id
  profile = "bx2-2x8"

  primary_network_interface {
    subnet = ibm_is_subnet.subnet.id
  }

  vpc  = ibm_is_vpc.vpc.id
  zone = var.ibm_zone
  keys = [data.ibm_is_ssh_key.ssh_key.id]
}##############################################################################
# Virtual Server Instance: 
# Migrated from VMware via RVTools
##############################################################################

resource "ibm_is_instance" "vaplqibmdb22-stg-va-hicloud" {
  name    = "vaplqibmdb22-stg-va-hicloud"
  image   = var.image_id
  profile = "bx2-2x8"

  primary_network_interface {
    subnet = ibm_is_subnet.subnet.id
  }

  vpc  = ibm_is_vpc.vpc.id
  zone = var.ibm_zone
  keys = [data.ibm_is_ssh_key.ssh_key.id]
}##############################################################################
# Virtual Server Instance: 
# Migrated from VMware via RVTools
##############################################################################

resource "ibm_is_instance" "vaplqmqiib01-stg-va-hicloud" {
  name    = "vaplqmqiib01-stg-va-hicloud"
  image   = var.image_id
  profile = "bx2-8x20"

  primary_network_interface {
    subnet = ibm_is_subnet.subnet.id
  }

  vpc  = ibm_is_vpc.vpc.id
  zone = var.ibm_zone
  keys = [data.ibm_is_ssh_key.ssh_key.id]
}##############################################################################
# Virtual Server Instance: 
# Migrated from VMware via RVTools
##############################################################################

resource "ibm_is_instance" "vaplqmqiib02-stg-va-hicloud" {
  name    = "vaplqmqiib02-stg-va-hicloud"
  image   = var.image_id
  profile = "bx2-8x20"

  primary_network_interface {
    subnet = ibm_is_subnet.subnet.id
  }

  vpc  = ibm_is_vpc.vpc.id
  zone = var.ibm_zone
  keys = [data.ibm_is_ssh_key.ssh_key.id]
}##############################################################################
# Virtual Server Instance: 
# Migrated from VMware via RVTools
##############################################################################

resource "ibm_is_instance" "vaplqmqp01-stg-va-hicloud" {
  name    = "vaplqmqp01-stg-va-hicloud"
  image   = var.image_id
  profile = "cx2-4x8"

  primary_network_interface {
    subnet = ibm_is_subnet.subnet.id
  }

  vpc  = ibm_is_vpc.vpc.id
  zone = var.ibm_zone
  keys = [data.ibm_is_ssh_key.ssh_key.id]
}##############################################################################
# Virtual Server Instance: 
# Migrated from VMware via RVTools
##############################################################################

resource "ibm_is_instance" "vaplqmqp02-stg-va-hicloud" {
  name    = "vaplqmqp02-stg-va-hicloud"
  image   = var.image_id
  profile = "cx2-4x8"

  primary_network_interface {
    subnet = ibm_is_subnet.subnet.id
  }

  vpc  = ibm_is_vpc.vpc.id
  zone = var.ibm_zone
  keys = [data.ibm_is_ssh_key.ssh_key.id]
}##############################################################################
# Virtual Server Instance: 
# Migrated from VMware via RVTools
##############################################################################

resource "ibm_is_instance" "vaplqwsrr01-stg-va-hicloud" {
  name    = "vaplqwsrr01-stg-va-hicloud"
  image   = var.image_id
  profile = "cx2-4x8"

  primary_network_interface {
    subnet = ibm_is_subnet.subnet.id
  }

  vpc  = ibm_is_vpc.vpc.id
  zone = var.ibm_zone
  keys = [data.ibm_is_ssh_key.ssh_key.id]
}##############################################################################
# Virtual Server Instance: 
# Migrated from VMware via RVTools
##############################################################################

resource "ibm_is_instance" "vaplqwsrr01-stg-va-hicloud_standby" {
  name    = "vaplqwsrr01-stg-va-hicloud_standby"
  image   = var.image_id
  profile = "cx2-4x8"

  primary_network_interface {
    subnet = ibm_is_subnet.subnet.id
  }

  vpc  = ibm_is_vpc.vpc.id
  zone = var.ibm_zone
  keys = [data.ibm_is_ssh_key.ssh_key.id]
}##############################################################################
# Virtual Server Instance: 
# Migrated from VMware via RVTools
##############################################################################

resource "ibm_is_instance" "vapltace01-sit-va-hicloud" {
  name    = "vapltace01-sit-va-hicloud"
  image   = var.image_id
  profile = "mx2-2x24"

  primary_network_interface {
    subnet = ibm_is_subnet.subnet.id
  }

  vpc  = ibm_is_vpc.vpc.id
  zone = var.ibm_zone
  keys = [data.ibm_is_ssh_key.ssh_key.id]
}##############################################################################
# Virtual Server Instance: 
# Migrated from VMware via RVTools
##############################################################################

resource "ibm_is_instance" "vapltcms01-sit-va-hicloud" {
  name    = "vapltcms01-sit-va-hicloud"
  image   = var.image_id
  profile = "cx2-2x4"

  primary_network_interface {
    subnet = ibm_is_subnet.subnet.id
  }

  vpc  = ibm_is_vpc.vpc.id
  zone = var.ibm_zone
  keys = [data.ibm_is_ssh_key.ssh_key.id]
}##############################################################################
# Virtual Server Instance: 
# Migrated from VMware via RVTools
##############################################################################

resource "ibm_is_instance" "vapltibmdb01-sit-va-hicloud" {
  name    = "vapltibmdb01-sit-va-hicloud"
  image   = var.image_id
  profile = "mx2-4x32"

  primary_network_interface {
    subnet = ibm_is_subnet.subnet.id
  }

  vpc  = ibm_is_vpc.vpc.id
  zone = var.ibm_zone
  keys = [data.ibm_is_ssh_key.ssh_key.id]
}##############################################################################
# Virtual Server Instance: 
# Migrated from VMware via RVTools
##############################################################################

resource "ibm_is_instance" "vapltibmdb21-sit-va-hicloud" {
  name    = "vapltibmdb21-sit-va-hicloud"
  image   = var.image_id
  profile = "bx2-2x6"

  primary_network_interface {
    subnet = ibm_is_subnet.subnet.id
  }

  vpc  = ibm_is_vpc.vpc.id
  zone = var.ibm_zone
  keys = [data.ibm_is_ssh_key.ssh_key.id]
}##############################################################################
# Virtual Server Instance: 
# Migrated from VMware via RVTools
##############################################################################

resource "ibm_is_instance" "vapltisds01-sit-va-hicloud" {
  name    = "vapltisds01-sit-va-hicloud"
  image   = var.image_id
  profile = "bx2-2x12"

  primary_network_interface {
    subnet = ibm_is_subnet.subnet.id
  }

  vpc  = ibm_is_vpc.vpc.id
  zone = var.ibm_zone
  keys = [data.ibm_is_ssh_key.ssh_key.id]
}##############################################################################
# Virtual Server Instance: 
# Migrated from VMware via RVTools
##############################################################################

resource "ibm_is_instance" "vapltmqiib01-sit-va-hicloud" {
  name    = "vapltmqiib01-sit-va-hicloud"
  image   = var.image_id
  profile = "bx2-4x24"

  primary_network_interface {
    subnet = ibm_is_subnet.subnet.id
  }

  vpc  = ibm_is_vpc.vpc.id
  zone = var.ibm_zone
  keys = [data.ibm_is_ssh_key.ssh_key.id]
}##############################################################################
# Virtual Server Instance: 
# Migrated from VMware via RVTools
##############################################################################

resource "ibm_is_instance" "vapltmqp01-sit-va-hicloud" {
  name    = "vapltmqp01-sit-va-hicloud"
  image   = var.image_id
  profile = "cx2-4x8"

  primary_network_interface {
    subnet = ibm_is_subnet.subnet.id
  }

  vpc  = ibm_is_vpc.vpc.id
  zone = var.ibm_zone
  keys = [data.ibm_is_ssh_key.ssh_key.id]
}##############################################################################
# Virtual Server Instance: 
# Migrated from VMware via RVTools
##############################################################################

resource "ibm_is_instance" "vapltport01-sit-va-hicloud" {
  name    = "vapltport01-sit-va-hicloud"
  image   = var.image_id
  profile = "cx2-2x4"

  primary_network_interface {
    subnet = ibm_is_subnet.subnet.id
  }

  vpc  = ibm_is_vpc.vpc.id
  zone = var.ibm_zone
  keys = [data.ibm_is_ssh_key.ssh_key.id]
}##############################################################################
# Virtual Server Instance: 
# Migrated from VMware via RVTools
##############################################################################

resource "ibm_is_instance" "vapltwsrr01-sit-va-hicloud" {
  name    = "vapltwsrr01-sit-va-hicloud"
  image   = var.image_id
  profile = "bx2-2x12"

  primary_network_interface {
    subnet = ibm_is_subnet.subnet.id
  }

  vpc  = ibm_is_vpc.vpc.id
  zone = var.ibm_zone
  keys = [data.ibm_is_ssh_key.ssh_key.id]
}##############################################################################
# Virtual Server Instance: 
# Migrated from VMware via RVTools
##############################################################################

resource "ibm_is_instance" "va-primary-nsxt-ctrlmgr0" {
  name    = "va-primary-nsxt-ctrlmgr0"
  image   = var.image_id
  profile = "bx2-6x24"

  primary_network_interface {
    subnet = ibm_is_subnet.subnet.id
  }

  vpc  = ibm_is_vpc.vpc.id
  zone = var.ibm_zone
  keys = [data.ibm_is_ssh_key.ssh_key.id]
}##############################################################################
# Virtual Server Instance: 
# Migrated from VMware via RVTools
##############################################################################

resource "ibm_is_instance" "va-primary-nsxt-ctrlmgr1" {
  name    = "va-primary-nsxt-ctrlmgr1"
  image   = var.image_id
  profile = "bx2-6x24"

  primary_network_interface {
    subnet = ibm_is_subnet.subnet.id
  }

  vpc  = ibm_is_vpc.vpc.id
  zone = var.ibm_zone
  keys = [data.ibm_is_ssh_key.ssh_key.id]
}##############################################################################
# Virtual Server Instance: 
# Migrated from VMware via RVTools
##############################################################################

resource "ibm_is_instance" "va-primary-nsxt-ctrlmgr2" {
  name    = "va-primary-nsxt-ctrlmgr2"
  image   = var.image_id
  profile = "bx2-6x24"

  primary_network_interface {
    subnet = ibm_is_subnet.subnet.id
  }

  vpc  = ibm_is_vpc.vpc.id
  zone = var.ibm_zone
  keys = [data.ibm_is_ssh_key.ssh_key.id]
}##############################################################################
# Virtual Server Instance: 
# Migrated from VMware via RVTools
##############################################################################

resource "ibm_is_instance" "va-primary-usage-meter-bcr-va-healthinteractive-net" {
  name    = "va-primary-usage-meter-bcr-va-healthinteractive-net"
  image   = var.image_id
  profile = "bx2-2x8"

  primary_network_interface {
    subnet = ibm_is_subnet.subnet.id
  }

  vpc  = ibm_is_vpc.vpc.id
  zone = var.ibm_zone
  keys = [data.ibm_is_ssh_key.ssh_key.id]
}##############################################################################
# Virtual Server Instance: 
# Migrated from VMware via RVTools
##############################################################################

resource "ibm_is_instance" "vapwpkx01-core-va-hicloud" {
  name    = "vapwpkx01-core-va-hicloud"
  image   = var.image_id
  profile = "cx2-4x8"

  primary_network_interface {
    subnet = ibm_is_subnet.subnet.id
  }

  vpc  = ibm_is_vpc.vpc.id
  zone = var.ibm_zone
  keys = [data.ibm_is_ssh_key.ssh_key.id]
}##############################################################################
# Virtual Server Instance: 
# Migrated from VMware via RVTools
##############################################################################

resource "ibm_is_instance" "vapwpkx01-core-va-hicloud_new" {
  name    = "vapwpkx01-core-va-hicloud_new"
  image   = var.image_id
  profile = "bx2-2x8"

  primary_network_interface {
    subnet = ibm_is_subnet.subnet.id
  }

  vpc  = ibm_is_vpc.vpc.id
  zone = var.ibm_zone
  keys = [data.ibm_is_ssh_key.ssh_key.id]
}##############################################################################
# Virtual Server Instance: 
# Migrated from VMware via RVTools
##############################################################################

resource "ibm_is_instance" "vbrp-repl01-bcr-va-healthinteractive-net" {
  name    = "vbrp-repl01-bcr-va-healthinteractive-net"
  image   = var.image_id
  profile = "cx2-8x8"

  primary_network_interface {
    subnet = ibm_is_subnet.subnet.id
  }

  vpc  = ibm_is_vpc.vpc.id
  zone = var.ibm_zone
  keys = [data.ibm_is_ssh_key.ssh_key.id]
}##############################################################################
# Virtual Server Instance: 
# Migrated from VMware via RVTools
##############################################################################

resource "ibm_is_instance" "vbrp-repl02-bcr-va-healthinteractive-net" {
  name    = "vbrp-repl02-bcr-va-healthinteractive-net"
  image   = var.image_id
  profile = "cx2-8x8"

  primary_network_interface {
    subnet = ibm_is_subnet.subnet.id
  }

  vpc  = ibm_is_vpc.vpc.id
  zone = var.ibm_zone
  keys = [data.ibm_is_ssh_key.ssh_key.id]
}##############################################################################
# Virtual Server Instance: 
# Migrated from VMware via RVTools
##############################################################################

resource "ibm_is_instance" "vcenter-8" {
  name    = "vcenter-8"
  image   = var.image_id
  profile = "bx2-8x30"

  primary_network_interface {
    subnet = ibm_is_subnet.subnet.id
  }

  vpc  = ibm_is_vpc.vpc.id
  zone = var.ibm_zone
  keys = [data.ibm_is_ssh_key.ssh_key.id]
}##############################################################################
# Virtual Server Instance: 
# Migrated from VMware via RVTools
##############################################################################

resource "ibm_is_instance" "vcenter-server-7-0" {
  name    = "vcenter-server-7-0"
  image   = var.image_id
  profile = "bx2-8x28"

  primary_network_interface {
    subnet = ibm_is_subnet.subnet.id
  }

  vpc  = ibm_is_vpc.vpc.id
  zone = var.ibm_zone
  keys = [data.ibm_is_ssh_key.ssh_key.id]
}##############################################################################
# Virtual Server Instance: 
# Migrated from VMware via RVTools
##############################################################################

resource "ibm_is_instance" "vrops-edge-1" {
  name    = "vrops-edge-1"
  image   = var.image_id
  profile = "cx2-4x8"

  primary_network_interface {
    subnet = ibm_is_subnet.subnet.id
  }

  vpc  = ibm_is_vpc.vpc.id
  zone = var.ibm_zone
  keys = [data.ibm_is_ssh_key.ssh_key.id]
}##############################################################################
# Virtual Server Instance: 
# Migrated from VMware via RVTools
##############################################################################

resource "ibm_is_instance" "vrops-edge-2" {
  name    = "vrops-edge-2"
  image   = var.image_id
  profile = "cx2-4x8"

  primary_network_interface {
    subnet = ibm_is_subnet.subnet.id
  }

  vpc  = ibm_is_vpc.vpc.id
  zone = var.ibm_zone
  keys = [data.ibm_is_ssh_key.ssh_key.id]
}##############################################################################
# Virtual Server Instance: 
# Migrated from VMware via RVTools
##############################################################################

resource "ibm_is_instance" "was-dev-va-hicloud" {
  name    = "was-dev-va-hicloud"
  image   = var.image_id
  profile = "bx2-2x8"

  primary_network_interface {
    subnet = ibm_is_subnet.subnet.id
  }

  vpc  = ibm_is_vpc.vpc.id
  zone = var.ibm_zone
  keys = [data.ibm_is_ssh_key.ssh_key.id]
}##############################################################################
# Virtual Server Instance: 
# Migrated from VMware via RVTools
##############################################################################

resource "ibm_is_instance" "was-prod-va-hicloud" {
  name    = "was-prod-va-hicloud"
  image   = var.image_id
  profile = "mx2-1x8"

  primary_network_interface {
    subnet = ibm_is_subnet.subnet.id
  }

  vpc  = ibm_is_vpc.vpc.id
  zone = var.ibm_zone
  keys = [data.ibm_is_ssh_key.ssh_key.id]
}##############################################################################
# Virtual Server Instance: 
# Migrated from VMware via RVTools
##############################################################################

resource "ibm_is_instance" "was-sit-va-hicloud" {
  name    = "was-sit-va-hicloud"
  image   = var.image_id
  profile = "mx2-1x12"

  primary_network_interface {
    subnet = ibm_is_subnet.subnet.id
  }

  vpc  = ibm_is_vpc.vpc.id
  zone = var.ibm_zone
  keys = [data.ibm_is_ssh_key.ssh_key.id]
}##############################################################################
# Virtual Server Instance: 
# Migrated from VMware via RVTools
##############################################################################

resource "ibm_is_instance" "was-stg-va-hicloud" {
  name    = "was-stg-va-hicloud"
  image   = var.image_id
  profile = "mx2-1x8"

  primary_network_interface {
    subnet = ibm_is_subnet.subnet.id
  }

  vpc  = ibm_is_vpc.vpc.id
  zone = var.ibm_zone
  keys = [data.ibm_is_ssh_key.ssh_key.id]
}##############################################################################
# Virtual Server Instance: 
# Migrated from VMware via RVTools
##############################################################################

resource "ibm_is_instance" "was1-prod-va-hicloud" {
  name    = "was1-prod-va-hicloud"
  image   = var.image_id
  profile = "mx2-1x8"

  primary_network_interface {
    subnet = ibm_is_subnet.subnet.id
  }

  vpc  = ibm_is_vpc.vpc.id
  zone = var.ibm_zone
  keys = [data.ibm_is_ssh_key.ssh_key.id]
}##############################################################################
# Virtual Server Instance: 
# Migrated from VMware via RVTools
##############################################################################

resource "ibm_is_instance" "was1-stg-va-hicloud" {
  name    = "was1-stg-va-hicloud"
  image   = var.image_id
  profile = "mx2-1x8"

  primary_network_interface {
    subnet = ibm_is_subnet.subnet.id
  }

  vpc  = ibm_is_vpc.vpc.id
  zone = var.ibm_zone
  keys = [data.ibm_is_ssh_key.ssh_key.id]
}##############################################################################
# Virtual Server Instance: 
# Migrated from VMware via RVTools
##############################################################################

resource "ibm_is_instance" "wasnd-portal-prod-va-hicloud" {
  name    = "wasnd-portal-prod-va-hicloud"
  image   = var.image_id
  profile = "cx2-4x8"

  primary_network_interface {
    subnet = ibm_is_subnet.subnet.id
  }

  vpc  = ibm_is_vpc.vpc.id
  zone = var.ibm_zone
  keys = [data.ibm_is_ssh_key.ssh_key.id]
}##############################################################################
# Virtual Server Instance: 
# Migrated from VMware via RVTools
##############################################################################

resource "ibm_is_instance" "wasnd-portal-stg-va-hicloud" {
  name    = "wasnd-portal-stg-va-hicloud"
  image   = var.image_id
  profile = "bx2-4x12"

  primary_network_interface {
    subnet = ibm_is_subnet.subnet.id
  }

  vpc  = ibm_is_vpc.vpc.id
  zone = var.ibm_zone
  keys = [data.ibm_is_ssh_key.ssh_key.id]
}##############################################################################
# Virtual Server Instance: 
# Migrated from VMware via RVTools
##############################################################################

resource "ibm_is_instance" "wasnd-portal1-prod-va-hicloud" {
  name    = "wasnd-portal1-prod-va-hicloud"
  image   = var.image_id
  profile = "cx2-4x8"

  primary_network_interface {
    subnet = ibm_is_subnet.subnet.id
  }

  vpc  = ibm_is_vpc.vpc.id
  zone = var.ibm_zone
  keys = [data.ibm_is_ssh_key.ssh_key.id]
}##############################################################################
# Virtual Server Instance: 
# Migrated from VMware via RVTools
##############################################################################

resource "ibm_is_instance" "wasnd-portal1-stg-va-hicloud" {
  name    = "wasnd-portal1-stg-va-hicloud"
  image   = var.image_id
  profile = "bx2-4x12"

  primary_network_interface {
    subnet = ibm_is_subnet.subnet.id
  }

  vpc  = ibm_is_vpc.vpc.id
  zone = var.ibm_zone
  keys = [data.ibm_is_ssh_key.ssh_key.id]
}##############################################################################
# Virtual Server Instance: 
# Migrated from VMware via RVTools
##############################################################################

resource "ibm_is_instance" "was-portal-sit-va-hicloud" {
  name    = "was-portal-sit-va-hicloud"
  image   = var.image_id
  profile = "bx2-2x12"

  primary_network_interface {
    subnet = ibm_is_subnet.subnet.id
  }

  vpc  = ibm_is_vpc.vpc.id
  zone = var.ibm_zone
  keys = [data.ibm_is_ssh_key.ssh_key.id]
}##############################################################################
# Virtual Server Instance: 
# Migrated from VMware via RVTools
##############################################################################

resource "ibm_is_instance" "webgateway-nonprod" {
  name    = "webgateway-nonprod"
  image   = var.image_id
  profile = "bx2-8x32"

  primary_network_interface {
    subnet = ibm_is_subnet.subnet.id
  }

  vpc  = ibm_is_vpc.vpc.id
  zone = var.ibm_zone
  keys = [data.ibm_is_ssh_key.ssh_key.id]
}##############################################################################
# Virtual Server Instance: 
# Migrated from VMware via RVTools
##############################################################################

resource "ibm_is_instance" "webmaint-dmz-va-hicloud" {
  name    = "webmaint-dmz-va-hicloud"
  image   = var.image_id
  profile = "cx2-2x4"

  primary_network_interface {
    subnet = ibm_is_subnet.subnet.id
  }

  vpc  = ibm_is_vpc.vpc.id
  zone = var.ibm_zone
  keys = [data.ibm_is_ssh_key.ssh_key.id]
}##############################################################################
# Virtual Server Instance: 
# Migrated from VMware via RVTools
##############################################################################

resource "ibm_is_instance" "webmaint-prod-va-hicloud" {
  name    = "webmaint-prod-va-hicloud"
  image   = var.image_id
  profile = "cx2-2x4"

  primary_network_interface {
    subnet = ibm_is_subnet.subnet.id
  }

  vpc  = ibm_is_vpc.vpc.id
  zone = var.ibm_zone
  keys = [data.ibm_is_ssh_key.ssh_key.id]
}##############################################################################
# Virtual Server Instance: 
# Migrated from VMware via RVTools
##############################################################################

resource "ibm_is_instance" "winutil-aisn-prod-va-hicloud" {
  name    = "winutil-aisn-prod-va-hicloud"
  image   = var.image_id
  profile = "cx2-2x4"

  primary_network_interface {
    subnet = ibm_is_subnet.subnet.id
  }

  vpc  = ibm_is_vpc.vpc.id
  zone = var.ibm_zone
  keys = [data.ibm_is_ssh_key.ssh_key.id]
}##############################################################################
# Virtual Server Instance: 
# Migrated from VMware via RVTools
##############################################################################

resource "ibm_is_instance" "winutility20-va-hicloud" {
  name    = "winutility20-va-hicloud"
  image   = var.image_id
  profile = "bx2-4x16"

  primary_network_interface {
    subnet = ibm_is_subnet.subnet.id
  }

  vpc  = ibm_is_vpc.vpc.id
  zone = var.ibm_zone
  keys = [data.ibm_is_ssh_key.ssh_key.id]
}##############################################################################
# Virtual Server Instance: 
# Migrated from VMware via RVTools
##############################################################################

resource "ibm_is_instance" "wsus01-va-hicloud" {
  name    = "wsus01-va-hicloud"
  image   = var.image_id
  profile = "bx2-4x16"

  primary_network_interface {
    subnet = ibm_is_subnet.subnet.id
  }

  vpc  = ibm_is_vpc.vpc.id
  zone = var.ibm_zone
  keys = [data.ibm_is_ssh_key.ssh_key.id]
}