
variable "ibm_region" {
  description = "The IBM Cloud region"
  type        = string
}

variable "ibm_zone" {
  description = "The specific zone within the region"
  type        = string
}

variable "prefix" {
  description = "A prefix for resource naming"
  type        = string
}

variable "image_id" {
  description = "The ID of the image to use for VSIs"
  type        = string
  default     = "r006-00000000-0000-0000-0000-000000000000"
}
