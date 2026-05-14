# VSI module for instance definitions

resource "ibm_is_instance" "app_01" {
  name    = "app_01-vsi"
  image   = var.custom_image_ids["app-01"]
  profile = "bx2-2x8"
  zone    = var.zone
  primary_network_interface {
    name   = "eth0"
    subnet = module.networking.app_net_id

    security_groups = [module.networking.app_net_sg_id]

  }

  tags = ["project:my-ibm-migration", "vm:app_01", "managed-by:rvtools-converter"]
}

resource "ibm_is_instance_volume_attachment" "app_01_hard_disk_2_attach" {
  instance = ibm_is_instance.app_01.id
  volume   = var.data_volume_ids["app_01"][0]
  name     = "app_01-hard_disk_2-attachment"
}
