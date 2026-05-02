variable "instance_type" {
    default = "t2.micro"
}

variable "key_name" {
    description = "SSH key name for EC2"
    type        = string
}

variable "bucket_name" {
    type = string
}
