variable "region" {
  type        = string
  description = "OCI region containing the pilot bucket."
}

variable "compartment_ocid" {
  type        = string
  description = "OCID of the team's development compartment."
}

variable "namespace" {
  type        = string
  description = "Object Storage namespace for the tenancy."
}

variable "bucket_name" {
  type        = string
  description = "Unique name of the private pilot bucket."
}

variable "common_tags" {
  type        = map(string)
  description = "Tags supplied by the team when tag_source is common_tags."
  default     = { environment = "dev" }
}
