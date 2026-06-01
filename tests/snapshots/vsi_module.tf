terraform {
  required_providers {
    ibm = {
      source  = "IBM-Cloud/ibm"
      version = ">= 1.70.0"
    }
  }
}

# VSI module for instance definitions

resource "ibm_is_instance" "app_01" {
  name    = "app-01-vsi"
  image   = var.custom_image_ids["app-01"]
  profile = "bx2-2x8"
  vpc     = var.vpc_id
  zone    = var.zone
  primary_network_interface {
    name   = "eth0"
    subnet = var.subnet_ids["app_net"]

    security_groups = [var.security_group_ids["app_net"]]

  }

  tags = ["project:my-ibm-migration", "vm:app_01", "managed-by:rvtools-converter"]
}

resource "ibm_is_instance_volume_attachment" "app_01_hard_disk_2_attach" {
  instance = ibm_is_instance.app_01.id
  volume   = var.data_volume_ids["app_01"][0]
  name     = "app-01-hard-disk-2-attachment"
}
