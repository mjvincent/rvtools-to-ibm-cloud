
resource "ibm_is_volume" "adminlinuxutilityserver-va-hicloud-disk-1" {
  name     = "adminlinuxutilityserver-va-hicloud-disk-1"
  profile  = "10iops-tier"
  zone     = "us-south-1"
  capacity = 55
}

resource "ibm_is_volume" "adminwindowsutilityserver-va-hicloud-disk-1" {
  name     = "adminwindowsutilityserver-va-hicloud-disk-1"
  profile  = "10iops-tier"
  zone     = "us-south-1"
  capacity = 200
}

resource "ibm_is_volume" "archive1-va-hicloud-disk-1" {
  name     = "archive1-va-hicloud-disk-1"
  profile  = "10iops-tier"
  zone     = "us-south-1"
  capacity = 100
}

resource "ibm_is_volume" "archive1-va-hicloud-disk-2" {
  name     = "archive1-va-hicloud-disk-2"
  profile  = "10iops-tier"
  zone     = "us-south-1"
  capacity = 72
}

resource "ibm_is_volume" "ca01-va-hicloud-disk-1" {
  name     = "ca01-va-hicloud-disk-1"
  profile  = "10iops-tier"
  zone     = "us-south-1"
  capacity = 40
}

resource "ibm_is_volume" "carbonblack-sensor-gateway-primary-disk-1" {
  name     = "carbonblack-sensor-gateway-primary-disk-1"
  profile  = "10iops-tier"
  zone     = "us-south-1"
  capacity = 10
}

resource "ibm_is_volume" "carbonblack-sensor-gateway-primary-disk-2" {
  name     = "carbonblack-sensor-gateway-primary-disk-2"
  profile  = "10iops-tier"
  zone     = "us-south-1"
  capacity = 10
}

resource "ibm_is_volume" "carbonblack-sensor-gateway-primary-disk-3" {
  name     = "carbonblack-sensor-gateway-primary-disk-3"
  profile  = "10iops-tier"
  zone     = "us-south-1"
  capacity = 10
}

resource "ibm_is_volume" "carbonblack-workoad-primary-disk-1" {
  name     = "carbonblack-workoad-primary-disk-1"
  profile  = "10iops-tier"
  zone     = "us-south-1"
  capacity = 5
}

resource "ibm_is_volume" "carbonblack-workoad-primary-disk-2" {
  name     = "carbonblack-workoad-primary-disk-2"
  profile  = "10iops-tier"
  zone     = "us-south-1"
  capacity = 20
}

resource "ibm_is_volume" "carbonblack-workoad-primary-disk-3" {
  name     = "carbonblack-workoad-primary-disk-3"
  profile  = "10iops-tier"
  zone     = "us-south-1"
  capacity = 4
}

resource "ibm_is_volume" "datapower-prod-va-hicloud-disk-1" {
  name     = "datapower-prod-va-hicloud-disk-1"
  profile  = "10iops-tier"
  zone     = "us-south-1"
  capacity = 32
}

resource "ibm_is_volume" "datapower-sit-va-hicloud-disk-1" {
  name     = "datapower-sit-va-hicloud-disk-1"
  profile  = "10iops-tier"
  zone     = "us-south-1"
  capacity = 32
}

resource "ibm_is_volume" "datapower-stg-va-hicloud-disk-1" {
  name     = "datapower-stg-va-hicloud-disk-1"
  profile  = "10iops-tier"
  zone     = "us-south-1"
  capacity = 32
}

resource "ibm_is_volume" "datapower1-prod-va-hicloud-disk-1" {
  name     = "datapower1-prod-va-hicloud-disk-1"
  profile  = "10iops-tier"
  zone     = "us-south-1"
  capacity = 32
}

resource "ibm_is_volume" "datapower1-stg-va-hicloud-disk-1" {
  name     = "datapower1-stg-va-hicloud-disk-1"
  profile  = "10iops-tier"
  zone     = "us-south-1"
  capacity = 32
}

resource "ibm_is_volume" "devutilwin01-dev-va-hicloud-disk-1" {
  name     = "devutilwin01-dev-va-hicloud-disk-1"
  profile  = "10iops-tier"
  zone     = "us-south-1"
  capacity = 110
}

resource "ibm_is_volume" "devutilwin02-sit-va-hicloud-disk-1" {
  name     = "devutilwin02-sit-va-hicloud-disk-1"
  profile  = "10iops-tier"
  zone     = "us-south-1"
  capacity = 100
}

resource "ibm_is_volume" "devutilwin03-stg-va-hicloud-disk-1" {
  name     = "devutilwin03-stg-va-hicloud-disk-1"
  profile  = "10iops-tier"
  zone     = "us-south-1"
  capacity = 150
}

resource "ibm_is_volume" "devutilwin04-prod-va-hicloud-disk-1" {
  name     = "devutilwin04-prod-va-hicloud-disk-1"
  profile  = "10iops-tier"
  zone     = "us-south-1"
  capacity = 135
}

resource "ibm_is_volume" "devutilwin10-va-hicloud-disk-1" {
  name     = "devutilwin10-va-hicloud-disk-1"
  profile  = "10iops-tier"
  zone     = "us-south-1"
  capacity = 100
}

resource "ibm_is_volume" "dns1-va-hicloud-disk-1" {
  name     = "dns1-va-hicloud-disk-1"
  profile  = "10iops-tier"
  zone     = "us-south-1"
  capacity = 5
}

resource "ibm_is_volume" "duo-auth-proxy-va-hicloud-disk-1" {
  name     = "duo-auth-proxy-va-hicloud-disk-1"
  profile  = "10iops-tier"
  zone     = "us-south-1"
  capacity = 5
}

resource "ibm_is_volume" "duo-auth-proxy-va-hicloud-disk-2" {
  name     = "duo-auth-proxy-va-hicloud-disk-2"
  profile  = "10iops-tier"
  zone     = "us-south-1"
  capacity = 5
}

resource "ibm_is_volume" "fg500d-backups-va-hicloud-disk-1" {
  name     = "fg500d-backups-va-hicloud-disk-1"
  profile  = "10iops-tier"
  zone     = "us-south-1"
  capacity = 20
}

resource "ibm_is_volume" "gitlab-va-hicloud-disk-1" {
  name     = "gitlab-va-hicloud-disk-1"
  profile  = "10iops-tier"
  zone     = "us-south-1"
  capacity = 50
}

resource "ibm_is_volume" "ilmt-va-hicloud-disk-1" {
  name     = "ilmt-va-hicloud-disk-1"
  profile  = "10iops-tier"
  zone     = "us-south-1"
  capacity = 100
}

resource "ibm_is_volume" "isvd01-dev-va-hicloud-disk-1" {
  name     = "isvd01-dev-va-hicloud-disk-1"
  profile  = "10iops-tier"
  zone     = "us-south-1"
  capacity = 30
}

resource "ibm_is_volume" "isvd01-dev-va-hicloud-disk-2" {
  name     = "isvd01-dev-va-hicloud-disk-2"
  profile  = "10iops-tier"
  zone     = "us-south-1"
  capacity = 61
}

resource "ibm_is_volume" "isvd01-prod-va-hicloud-disk-1" {
  name     = "isvd01-prod-va-hicloud-disk-1"
  profile  = "10iops-tier"
  zone     = "us-south-1"
  capacity = 61
}

resource "ibm_is_volume" "isvd01-prod-va-hicloud-disk-2" {
  name     = "isvd01-prod-va-hicloud-disk-2"
  profile  = "10iops-tier"
  zone     = "us-south-1"
  capacity = 50
}

resource "ibm_is_volume" "isvd01-sit-va-hicloud-disk-1" {
  name     = "isvd01-sit-va-hicloud-disk-1"
  profile  = "10iops-tier"
  zone     = "us-south-1"
  capacity = 30
}

resource "ibm_is_volume" "isvd01-sit-va-hicloud-disk-2" {
  name     = "isvd01-sit-va-hicloud-disk-2"
  profile  = "10iops-tier"
  zone     = "us-south-1"
  capacity = 61
}

resource "ibm_is_volume" "isvd01-stg-va-hicloud-disk-1" {
  name     = "isvd01-stg-va-hicloud-disk-1"
  profile  = "10iops-tier"
  zone     = "us-south-1"
  capacity = 65
}

resource "ibm_is_volume" "isvd02-prod-va-hicloud-disk-1" {
  name     = "isvd02-prod-va-hicloud-disk-1"
  profile  = "10iops-tier"
  zone     = "us-south-1"
  capacity = 60
}

resource "ibm_is_volume" "isvd02-prod-va-hicloud-disk-2" {
  name     = "isvd02-prod-va-hicloud-disk-2"
  profile  = "10iops-tier"
  zone     = "us-south-1"
  capacity = 50
}

resource "ibm_is_volume" "isvd02-stg-va-hicloud-disk-1" {
  name     = "isvd02-stg-va-hicloud-disk-1"
  profile  = "10iops-tier"
  zone     = "us-south-1"
  capacity = 65
}

resource "ibm_is_volume" "jenkins-va-hicloud-disk-1" {
  name     = "jenkins-va-hicloud-disk-1"
  profile  = "10iops-tier"
  zone     = "us-south-1"
  capacity = 80
}

resource "ibm_is_volume" "jira-va-hicloud-disk-1" {
  name     = "jira-va-hicloud-disk-1"
  profile  = "10iops-tier"
  zone     = "us-south-1"
  capacity = 50
}

resource "ibm_is_volume" "jira-va-hicloud-disk-2" {
  name     = "jira-va-hicloud-disk-2"
  profile  = "10iops-tier"
  zone     = "us-south-1"
  capacity = 25
}

resource "ibm_is_volume" "moveit-auto-va-hicloud-disk-1" {
  name     = "moveit-auto-va-hicloud-disk-1"
  profile  = "10iops-tier"
  zone     = "us-south-1"
  capacity = 500
}

resource "ibm_is_volume" "moveit-auto-va-hicloud-disk-2" {
  name     = "moveit-auto-va-hicloud-disk-2"
  profile  = "10iops-tier"
  zone     = "us-south-1"
  capacity = 500
}

resource "ibm_is_volume" "moveit-auto-va-hicloud-disk-3" {
  name     = "moveit-auto-va-hicloud-disk-3"
  profile  = "10iops-tier"
  zone     = "us-south-1"
  capacity = 500
}

resource "ibm_is_volume" "moveit-auto-va-hicloud-disk-4" {
  name     = "moveit-auto-va-hicloud-disk-4"
  profile  = "10iops-tier"
  zone     = "us-south-1"
  capacity = 500
}

resource "ibm_is_volume" "moveit-central-prod-va-hicloud-disk-1" {
  name     = "moveit-central-prod-va-hicloud-disk-1"
  profile  = "10iops-tier"
  zone     = "us-south-1"
  capacity = 500
}

resource "ibm_is_volume" "moveit-central-prod-va-hicloud-disk-2" {
  name     = "moveit-central-prod-va-hicloud-disk-2"
  profile  = "10iops-tier"
  zone     = "us-south-1"
  capacity = 500
}

resource "ibm_is_volume" "moveit-central-prod-va-hicloud_standby-disk-1" {
  name     = "moveit-central-prod-va-hicloud_standby-disk-1"
  profile  = "10iops-tier"
  zone     = "us-south-1"
  capacity = 500
}

resource "ibm_is_volume" "moveit-central-prod-va-hicloud_standby-disk-2" {
  name     = "moveit-central-prod-va-hicloud_standby-disk-2"
  profile  = "10iops-tier"
  zone     = "us-south-1"
  capacity = 500
}

resource "ibm_is_volume" "moveit-dmz-dmz-va-hicloud-disk-1" {
  name     = "moveit-dmz-dmz-va-hicloud-disk-1"
  profile  = "10iops-tier"
  zone     = "us-south-1"
  capacity = 600
}

resource "ibm_is_volume" "moveit-mft-prod-va-hicloud-disk-1" {
  name     = "moveit-mft-prod-va-hicloud-disk-1"
  profile  = "10iops-tier"
  zone     = "us-south-1"
  capacity = 1120
}

resource "ibm_is_volume" "moveit-mft-prod-va-hicloud_standby-disk-1" {
  name     = "moveit-mft-prod-va-hicloud_standby-disk-1"
  profile  = "10iops-tier"
  zone     = "us-south-1"
  capacity = 1120
}

resource "ibm_is_volume" "sftp01-va-hicloud-disk-1" {
  name     = "sftp01-va-hicloud-disk-1"
  profile  = "10iops-tier"
  zone     = "us-south-1"
  capacity = 30
}

resource "ibm_is_volume" "sgw-va-1-2-1-0-24042317_ovf10-disk-1" {
  name     = "sgw-va-1-2-1-0-24042317_ovf10-disk-1"
  profile  = "10iops-tier"
  zone     = "us-south-1"
  capacity = 10
}

resource "ibm_is_volume" "sgw-va-1-2-1-0-24042317_ovf10-disk-2" {
  name     = "sgw-va-1-2-1-0-24042317_ovf10-disk-2"
  profile  = "10iops-tier"
  zone     = "us-south-1"
  capacity = 10
}

resource "ibm_is_volume" "sgw-va-1-2-1-0-24042317_ovf10-disk-3" {
  name     = "sgw-va-1-2-1-0-24042317_ovf10-disk-3"
  profile  = "10iops-tier"
  zone     = "us-south-1"
  capacity = 10
}

resource "ibm_is_volume" "splunkdevdeployment-va-hicloud-disk-1" {
  name     = "splunkdevdeployment-va-hicloud-disk-1"
  profile  = "10iops-tier"
  zone     = "us-south-1"
  capacity = 50
}

resource "ibm_is_volume" "splunkdevhf-va-hicloud-disk-1" {
  name     = "splunkdevhf-va-hicloud-disk-1"
  profile  = "10iops-tier"
  zone     = "us-south-1"
  capacity = 50
}

resource "ibm_is_volume" "splunkdevindexer1-va-hicloud-disk-1" {
  name     = "splunkdevindexer1-va-hicloud-disk-1"
  profile  = "10iops-tier"
  zone     = "us-south-1"
  capacity = 250
}

resource "ibm_is_volume" "splunkdevindexer1-va-hicloud-disk-2" {
  name     = "splunkdevindexer1-va-hicloud-disk-2"
  profile  = "10iops-tier"
  zone     = "us-south-1"
  capacity = 100
}

resource "ibm_is_volume" "splunkes-va-hicloud-disk-1" {
  name     = "splunkes-va-hicloud-disk-1"
  profile  = "10iops-tier"
  zone     = "us-south-1"
  capacity = 128
}

resource "ibm_is_volume" "splunkindexer1-va-hicloud-disk-1" {
  name     = "splunkindexer1-va-hicloud-disk-1"
  profile  = "10iops-tier"
  zone     = "us-south-1"
  capacity = 1638
}

resource "ibm_is_volume" "splunkindexer1-va-hicloud-disk-2" {
  name     = "splunkindexer1-va-hicloud-disk-2"
  profile  = "10iops-tier"
  zone     = "us-south-1"
  capacity = 2150
}

resource "ibm_is_volume" "splunkindexer2-va-hicloud-disk-1" {
  name     = "splunkindexer2-va-hicloud-disk-1"
  profile  = "10iops-tier"
  zone     = "us-south-1"
  capacity = 1500
}

resource "ibm_is_volume" "splunkindexer2-va-hicloud-disk-2" {
  name     = "splunkindexer2-va-hicloud-disk-2"
  profile  = "10iops-tier"
  zone     = "us-south-1"
  capacity = 2150
}

resource "ibm_is_volume" "splunklicensemaster-va-hicloud-disk-1" {
  name     = "splunklicensemaster-va-hicloud-disk-1"
  profile  = "10iops-tier"
  zone     = "us-south-1"
  capacity = 900
}

resource "ibm_is_volume" "splunklicensemaster-va-hicloud-disk-2" {
  name     = "splunklicensemaster-va-hicloud-disk-2"
  profile  = "10iops-tier"
  zone     = "us-south-1"
  capacity = 50
}

resource "ibm_is_volume" "symantec-2-va-hicloud-disk-1" {
  name     = "symantec-2-va-hicloud-disk-1"
  profile  = "10iops-tier"
  zone     = "us-south-1"
  capacity = 200
}

resource "ibm_is_volume" "symc1-prod-va-hicloud-disk-1" {
  name     = "symc1-prod-va-hicloud-disk-1"
  profile  = "10iops-tier"
  zone     = "us-south-1"
  capacity = 220
}

resource "ibm_is_volume" "vapldace01-dev-va-hicloud-disk-1" {
  name     = "vapldace01-dev-va-hicloud-disk-1"
  profile  = "10iops-tier"
  zone     = "us-south-1"
  capacity = 150
}

resource "ibm_is_volume" "vapldcsvn01-dev-va-hicloud-disk-1" {
  name     = "vapldcsvn01-dev-va-hicloud-disk-1"
  profile  = "10iops-tier"
  zone     = "us-south-1"
  capacity = 25
}

resource "ibm_is_volume" "vapldibmdb01-dev-va-hicloud-disk-1" {
  name     = "vapldibmdb01-dev-va-hicloud-disk-1"
  profile  = "10iops-tier"
  zone     = "us-south-1"
  capacity = 500
}

resource "ibm_is_volume" "vapldlbas01-dev-va-hicloud-disk-1" {
  name     = "vapldlbas01-dev-va-hicloud-disk-1"
  profile  = "10iops-tier"
  zone     = "us-south-1"
  capacity = 50
}

resource "ibm_is_volume" "vapldmq01-dev-va-hicloud-disk-1" {
  name     = "vapldmq01-dev-va-hicloud-disk-1"
  profile  = "10iops-tier"
  zone     = "us-south-1"
  capacity = 80
}

resource "ibm_is_volume" "vapldmqp01-dev-va-hicloud-disk-1" {
  name     = "vapldmqp01-dev-va-hicloud-disk-1"
  profile  = "10iops-tier"
  zone     = "us-south-1"
  capacity = 80
}

resource "ibm_is_volume" "vapldport01-dev-va-hicloud-disk-1" {
  name     = "vapldport01-dev-va-hicloud-disk-1"
  profile  = "10iops-tier"
  zone     = "us-south-1"
  capacity = 50
}

resource "ibm_is_volume" "vapldwas01-dev-va-hicloud-disk-1" {
  name     = "vapldwas01-dev-va-hicloud-disk-1"
  profile  = "10iops-tier"
  zone     = "us-south-1"
  capacity = 12
}

resource "ibm_is_volume" "vapldwsrr01-dev-va-hicloud-disk-1" {
  name     = "vapldwsrr01-dev-va-hicloud-disk-1"
  profile  = "10iops-tier"
  zone     = "us-south-1"
  capacity = 30
}

resource "ibm_is_volume" "vaplnspdep11-va-hicloud-disk-1" {
  name     = "vaplnspdep11-va-hicloud-disk-1"
  profile  = "10iops-tier"
  zone     = "us-south-1"
  capacity = 60
}

resource "ibm_is_volume" "vaplnsphf11-va-hicloud-disk-1" {
  name     = "vaplnsphf11-va-hicloud-disk-1"
  profile  = "10iops-tier"
  zone     = "us-south-1"
  capacity = 60
}

resource "ibm_is_volume" "vaplnspin11-va-hicloud-disk-1" {
  name     = "vaplnspin11-va-hicloud-disk-1"
  profile  = "10iops-tier"
  zone     = "us-south-1"
  capacity = 560
}

resource "ibm_is_volume" "vaplpace01-prod-va-hicloud-disk-1" {
  name     = "vaplpace01-prod-va-hicloud-disk-1"
  profile  = "10iops-tier"
  zone     = "us-south-1"
  capacity = 150
}

resource "ibm_is_volume" "vaplpace02-prod-va-hicloud-disk-1" {
  name     = "vaplpace02-prod-va-hicloud-disk-1"
  profile  = "10iops-tier"
  zone     = "us-south-1"
  capacity = 150
}

resource "ibm_is_volume" "vaplparch01-va-hicloud-disk-1" {
  name     = "vaplparch01-va-hicloud-disk-1"
  profile  = "10iops-tier"
  zone     = "us-south-1"
  capacity = 200
}

resource "ibm_is_volume" "vaplpcms01-prod-va-hicloud-disk-1" {
  name     = "vaplpcms01-prod-va-hicloud-disk-1"
  profile  = "10iops-tier"
  zone     = "us-south-1"
  capacity = 86
}

resource "ibm_is_volume" "vaplpcms02-prod-va-hicloud-disk-1" {
  name     = "vaplpcms02-prod-va-hicloud-disk-1"
  profile  = "10iops-tier"
  zone     = "us-south-1"
  capacity = 86
}

resource "ibm_is_volume" "vaplpdns01-va-hicloud-disk-1" {
  name     = "vaplpdns01-va-hicloud-disk-1"
  profile  = "10iops-tier"
  zone     = "us-south-1"
  capacity = 10
}

resource "ibm_is_volume" "vaplpdns02-va-hicloud-disk-1" {
  name     = "vaplpdns02-va-hicloud-disk-1"
  profile  = "10iops-tier"
  zone     = "us-south-1"
  capacity = 10
}

resource "ibm_is_volume" "vaplpduo01-core-va-hicloud-disk-1" {
  name     = "vaplpduo01-core-va-hicloud-disk-1"
  profile  = "10iops-tier"
  zone     = "us-south-1"
  capacity = 34
}

resource "ibm_is_volume" "vaplpibmdb01-prod-va-hicloud-disk-1" {
  name     = "vaplpibmdb01-prod-va-hicloud-disk-1"
  profile  = "10iops-tier"
  zone     = "us-south-1"
  capacity = 1710
}

resource "ibm_is_volume" "vaplpibmdb02-prod-va-hicloud-disk-1" {
  name     = "vaplpibmdb02-prod-va-hicloud-disk-1"
  profile  = "10iops-tier"
  zone     = "us-south-1"
  capacity = 1710
}

resource "ibm_is_volume" "vaplpibmdb21-prod-va-hicloud-disk-1" {
  name     = "vaplpibmdb21-prod-va-hicloud-disk-1"
  profile  = "10iops-tier"
  zone     = "us-south-1"
  capacity = 520
}

resource "ibm_is_volume" "vaplpibmdb22-prod-va-hicloud-disk-1" {
  name     = "vaplpibmdb22-prod-va-hicloud-disk-1"
  profile  = "10iops-tier"
  zone     = "us-south-1"
  capacity = 490
}

resource "ibm_is_volume" "vaplpjen01-core-va-hicloud-disk-1" {
  name     = "vaplpjen01-core-va-hicloud-disk-1"
  profile  = "10iops-tier"
  zone     = "us-south-1"
  capacity = 90
}

resource "ibm_is_volume" "vaplpjira01-core-va-hicloud-disk-1" {
  name     = "vaplpjira01-core-va-hicloud-disk-1"
  profile  = "10iops-tier"
  zone     = "us-south-1"
  capacity = 123
}

resource "ibm_is_volume" "vaplplbas01-va-hicloud-disk-1" {
  name     = "vaplplbas01-va-hicloud-disk-1"
  profile  = "10iops-tier"
  zone     = "us-south-1"
  capacity = 10
}

resource "ibm_is_volume" "vaplpmpage01-prod-va-hicloud_don't-delete-disk-1" {
  name     = "vaplpmpage01-prod-va-hicloud_don't-delete-disk-1"
  profile  = "10iops-tier"
  zone     = "us-south-1"
  capacity = 50
}

resource "ibm_is_volume" "vaplpmq01-prod-va-hicloud-disk-1" {
  name     = "vaplpmq01-prod-va-hicloud-disk-1"
  profile  = "10iops-tier"
  zone     = "us-south-1"
  capacity = 102
}

resource "ibm_is_volume" "vaplpmq02-prod-va-hicloud-disk-1" {
  name     = "vaplpmq02-prod-va-hicloud-disk-1"
  profile  = "10iops-tier"
  zone     = "us-south-1"
  capacity = 102
}

resource "ibm_is_volume" "vaplpmqp01-prod-va-hicloud-disk-1" {
  name     = "vaplpmqp01-prod-va-hicloud-disk-1"
  profile  = "10iops-tier"
  zone     = "us-south-1"
  capacity = 102
}

resource "ibm_is_volume" "vaplpmqp02-prod-va-hicloud-disk-1" {
  name     = "vaplpmqp02-prod-va-hicloud-disk-1"
  profile  = "10iops-tier"
  zone     = "us-south-1"
  capacity = 102
}

resource "ibm_is_volume" "vaplpmysql01-core-va-hicloud-disk-1" {
  name     = "vaplpmysql01-core-va-hicloud-disk-1"
  profile  = "10iops-tier"
  zone     = "us-south-1"
  capacity = 76
}

resource "ibm_is_volume" "vaplpnagios01-va-hicloud-disk-1" {
  name     = "vaplpnagios01-va-hicloud-disk-1"
  profile  = "10iops-tier"
  zone     = "us-south-1"
  capacity = 10
}

resource "ibm_is_volume" "vaplpnas01-va-hicloud-disk-1" {
  name     = "vaplpnas01-va-hicloud-disk-1"
  profile  = "10iops-tier"
  zone     = "us-south-1"
  capacity = 2
}

resource "ibm_is_volume" "vaplpnas01-va-hicloud-disk-2" {
  name     = "vaplpnas01-va-hicloud-disk-2"
  profile  = "10iops-tier"
  zone     = "us-south-1"
  capacity = 700
}

resource "ibm_is_volume" "vaplpntpsrv01-va-hicloud-disk-1" {
  name     = "vaplpntpsrv01-va-hicloud-disk-1"
  profile  = "10iops-tier"
  zone     = "us-south-1"
  capacity = 10
}

resource "ibm_is_volume" "vaplprhrepo01-va-hicloud-disk-1" {
  name     = "vaplprhrepo01-va-hicloud-disk-1"
  profile  = "10iops-tier"
  zone     = "us-south-1"
  capacity = 60
}

resource "ibm_is_volume" "vaplprhrepo01-va-hicloud-disk-2" {
  name     = "vaplprhrepo01-va-hicloud-disk-2"
  profile  = "10iops-tier"
  zone     = "us-south-1"
  capacity = 10
}

resource "ibm_is_volume" "vaplpslog01-va-hicloud-disk-1" {
  name     = "vaplpslog01-va-hicloud-disk-1"
  profile  = "10iops-tier"
  zone     = "us-south-1"
  capacity = 10
}

resource "ibm_is_volume" "vaplpslog01-va-hicloud-disk-2" {
  name     = "vaplpslog01-va-hicloud-disk-2"
  profile  = "10iops-tier"
  zone     = "us-south-1"
  capacity = 980
}

resource "ibm_is_volume" "vaplpsmtp01-va-hicloud-disk-1" {
  name     = "vaplpsmtp01-va-hicloud-disk-1"
  profile  = "10iops-tier"
  zone     = "us-south-1"
  capacity = 10
}

resource "ibm_is_volume" "vaplpsp01-va-hicloud-disk-1" {
  name     = "vaplpsp01-va-hicloud-disk-1"
  profile  = "10iops-tier"
  zone     = "us-south-1"
  capacity = 60
}

resource "ibm_is_volume" "vaplpspdep01-va-hicloud-disk-1" {
  name     = "vaplpspdep01-va-hicloud-disk-1"
  profile  = "10iops-tier"
  zone     = "us-south-1"
  capacity = 60
}

resource "ibm_is_volume" "vaplpspes01-va-hicloud-disk-1" {
  name     = "vaplpspes01-va-hicloud-disk-1"
  profile  = "10iops-tier"
  zone     = "us-south-1"
  capacity = 80
}

resource "ibm_is_volume" "vaplpsphf01-va-hicloud-disk-1" {
  name     = "vaplpsphf01-va-hicloud-disk-1"
  profile  = "10iops-tier"
  zone     = "us-south-1"
  capacity = 60
}

resource "ibm_is_volume" "vaplpspim01-va-hicloud-disk-1" {
  name     = "vaplpspim01-va-hicloud-disk-1"
  profile  = "10iops-tier"
  zone     = "us-south-1"
  capacity = 60
}

resource "ibm_is_volume" "vaplpspin01-va-hicloud-disk-1" {
  name     = "vaplpspin01-va-hicloud-disk-1"
  profile  = "10iops-tier"
  zone     = "us-south-1"
  capacity = 2620
}

resource "ibm_is_volume" "vaplpspin02-va-hicloud-disk-1" {
  name     = "vaplpspin02-va-hicloud-disk-1"
  profile  = "10iops-tier"
  zone     = "us-south-1"
  capacity = 2620
}

resource "ibm_is_volume" "vaplpspxy01-va-hicloud-disk-1" {
  name     = "vaplpspxy01-va-hicloud-disk-1"
  profile  = "10iops-tier"
  zone     = "us-south-1"
  capacity = 10
}

resource "ibm_is_volume" "vaplpurldir01-prod-va-hicloud-disk-1" {
  name     = "vaplpurldir01-prod-va-hicloud-disk-1"
  profile  = "10iops-tier"
  zone     = "us-south-1"
  capacity = 34
}

resource "ibm_is_volume" "vaplpurldir02-prod-va-hicloud-disk-1" {
  name     = "vaplpurldir02-prod-va-hicloud-disk-1"
  profile  = "10iops-tier"
  zone     = "us-south-1"
  capacity = 34
}

resource "ibm_is_volume" "vaplpwsrr01-prod-va-hicloud-disk-1" {
  name     = "vaplpwsrr01-prod-va-hicloud-disk-1"
  profile  = "10iops-tier"
  zone     = "us-south-1"
  capacity = 55
}

resource "ibm_is_volume" "vaplpwsrr01-prod-va-hicloud_standby-disk-1" {
  name     = "vaplpwsrr01-prod-va-hicloud_standby-disk-1"
  profile  = "10iops-tier"
  zone     = "us-south-1"
  capacity = 55
}

resource "ibm_is_volume" "vaplqace01-stg-va-hicloud-disk-1" {
  name     = "vaplqace01-stg-va-hicloud-disk-1"
  profile  = "10iops-tier"
  zone     = "us-south-1"
  capacity = 202
}

resource "ibm_is_volume" "vaplqace02-stg-va-hicloud-disk-1" {
  name     = "vaplqace02-stg-va-hicloud-disk-1"
  profile  = "10iops-tier"
  zone     = "us-south-1"
  capacity = 202
}

resource "ibm_is_volume" "vaplqcms01-stg-va-hicloud-disk-1" {
  name     = "vaplqcms01-stg-va-hicloud-disk-1"
  profile  = "10iops-tier"
  zone     = "us-south-1"
  capacity = 86
}

resource "ibm_is_volume" "vaplqcms02-stg-va-hicloud-disk-1" {
  name     = "vaplqcms02-stg-va-hicloud-disk-1"
  profile  = "10iops-tier"
  zone     = "us-south-1"
  capacity = 86
}

resource "ibm_is_volume" "vaplqibmdb01-stg-va-hicloud-disk-1" {
  name     = "vaplqibmdb01-stg-va-hicloud-disk-1"
  profile  = "10iops-tier"
  zone     = "us-south-1"
  capacity = 1230
}

resource "ibm_is_volume" "vaplqibmdb02-stg-va-hicloud-disk-1" {
  name     = "vaplqibmdb02-stg-va-hicloud-disk-1"
  profile  = "10iops-tier"
  zone     = "us-south-1"
  capacity = 1230
}

resource "ibm_is_volume" "vaplqibmdb21-stg-va-hicloud-disk-1" {
  name     = "vaplqibmdb21-stg-va-hicloud-disk-1"
  profile  = "10iops-tier"
  zone     = "us-south-1"
  capacity = 390
}

resource "ibm_is_volume" "vaplqibmdb22-stg-va-hicloud-disk-1" {
  name     = "vaplqibmdb22-stg-va-hicloud-disk-1"
  profile  = "10iops-tier"
  zone     = "us-south-1"
  capacity = 390
}

resource "ibm_is_volume" "vaplqmqiib01-stg-va-hicloud-disk-1" {
  name     = "vaplqmqiib01-stg-va-hicloud-disk-1"
  profile  = "10iops-tier"
  zone     = "us-south-1"
  capacity = 102
}

resource "ibm_is_volume" "vaplqmqiib02-stg-va-hicloud-disk-1" {
  name     = "vaplqmqiib02-stg-va-hicloud-disk-1"
  profile  = "10iops-tier"
  zone     = "us-south-1"
  capacity = 102
}

resource "ibm_is_volume" "vaplqmqp01-stg-va-hicloud-disk-1" {
  name     = "vaplqmqp01-stg-va-hicloud-disk-1"
  profile  = "10iops-tier"
  zone     = "us-south-1"
  capacity = 102
}

resource "ibm_is_volume" "vaplqmqp02-stg-va-hicloud-disk-1" {
  name     = "vaplqmqp02-stg-va-hicloud-disk-1"
  profile  = "10iops-tier"
  zone     = "us-south-1"
  capacity = 102
}

resource "ibm_is_volume" "vaplqwsrr01-stg-va-hicloud-disk-1" {
  name     = "vaplqwsrr01-stg-va-hicloud-disk-1"
  profile  = "10iops-tier"
  zone     = "us-south-1"
  capacity = 90
}

resource "ibm_is_volume" "vaplqwsrr01-stg-va-hicloud_standby-disk-1" {
  name     = "vaplqwsrr01-stg-va-hicloud_standby-disk-1"
  profile  = "10iops-tier"
  zone     = "us-south-1"
  capacity = 90
}

resource "ibm_is_volume" "vapltace01-sit-va-hicloud-disk-1" {
  name     = "vapltace01-sit-va-hicloud-disk-1"
  profile  = "10iops-tier"
  zone     = "us-south-1"
  capacity = 62
}

resource "ibm_is_volume" "vapltcms01-sit-va-hicloud-disk-1" {
  name     = "vapltcms01-sit-va-hicloud-disk-1"
  profile  = "10iops-tier"
  zone     = "us-south-1"
  capacity = 86
}

resource "ibm_is_volume" "vapltibmdb01-sit-va-hicloud-disk-1" {
  name     = "vapltibmdb01-sit-va-hicloud-disk-1"
  profile  = "10iops-tier"
  zone     = "us-south-1"
  capacity = 440
}

resource "ibm_is_volume" "vapltibmdb21-sit-va-hicloud-disk-1" {
  name     = "vapltibmdb21-sit-va-hicloud-disk-1"
  profile  = "10iops-tier"
  zone     = "us-south-1"
  capacity = 390
}

resource "ibm_is_volume" "vapltisds01-sit-va-hicloud-disk-1" {
  name     = "vapltisds01-sit-va-hicloud-disk-1"
  profile  = "10iops-tier"
  zone     = "us-south-1"
  capacity = 34
}

resource "ibm_is_volume" "vapltmqiib01-sit-va-hicloud-disk-1" {
  name     = "vapltmqiib01-sit-va-hicloud-disk-1"
  profile  = "10iops-tier"
  zone     = "us-south-1"
  capacity = 34
}

resource "ibm_is_volume" "vapltmqp01-sit-va-hicloud-disk-1" {
  name     = "vapltmqp01-sit-va-hicloud-disk-1"
  profile  = "10iops-tier"
  zone     = "us-south-1"
  capacity = 34
}

resource "ibm_is_volume" "vapltport01-sit-va-hicloud-disk-1" {
  name     = "vapltport01-sit-va-hicloud-disk-1"
  profile  = "10iops-tier"
  zone     = "us-south-1"
  capacity = 80
}

resource "ibm_is_volume" "vapltwsrr01-sit-va-hicloud-disk-1" {
  name     = "vapltwsrr01-sit-va-hicloud-disk-1"
  profile  = "10iops-tier"
  zone     = "us-south-1"
  capacity = 100
}

resource "ibm_is_volume" "va-primary-nsxt-ctrlmgr0-disk-1" {
  name     = "va-primary-nsxt-ctrlmgr0-disk-1"
  profile  = "10iops-tier"
  zone     = "us-south-1"
  capacity = 100
}

resource "ibm_is_volume" "va-primary-nsxt-ctrlmgr1-disk-1" {
  name     = "va-primary-nsxt-ctrlmgr1-disk-1"
  profile  = "10iops-tier"
  zone     = "us-south-1"
  capacity = 100
}

resource "ibm_is_volume" "va-primary-nsxt-ctrlmgr2-disk-1" {
  name     = "va-primary-nsxt-ctrlmgr2-disk-1"
  profile  = "10iops-tier"
  zone     = "us-south-1"
  capacity = 100
}

resource "ibm_is_volume" "vapwpkx01-core-va-hicloud-disk-1" {
  name     = "vapwpkx01-core-va-hicloud-disk-1"
  profile  = "10iops-tier"
  zone     = "us-south-1"
  capacity = 100
}

resource "ibm_is_volume" "vapwpkx01-core-va-hicloud-disk-2" {
  name     = "vapwpkx01-core-va-hicloud-disk-2"
  profile  = "10iops-tier"
  zone     = "us-south-1"
  capacity = 100
}

resource "ibm_is_volume" "vbrp-repl01-bcr-va-healthinteractive-net-disk-1" {
  name     = "vbrp-repl01-bcr-va-healthinteractive-net-disk-1"
  profile  = "10iops-tier"
  zone     = "us-south-1"
  capacity = 800
}

resource "ibm_is_volume" "vcenter-8-disk-1" {
  name     = "vcenter-8-disk-1"
  profile  = "10iops-tier"
  zone     = "us-south-1"
  capacity = 7
}

resource "ibm_is_volume" "vcenter-8-disk-2" {
  name     = "vcenter-8-disk-2"
  profile  = "10iops-tier"
  zone     = "us-south-1"
  capacity = 50
}

resource "ibm_is_volume" "vcenter-8-disk-3" {
  name     = "vcenter-8-disk-3"
  profile  = "10iops-tier"
  zone     = "us-south-1"
  capacity = 50
}

resource "ibm_is_volume" "vcenter-8-disk-4" {
  name     = "vcenter-8-disk-4"
  profile  = "10iops-tier"
  zone     = "us-south-1"
  capacity = 25
}

resource "ibm_is_volume" "vcenter-8-disk-5" {
  name     = "vcenter-8-disk-5"
  profile  = "10iops-tier"
  zone     = "us-south-1"
  capacity = 25
}

resource "ibm_is_volume" "vcenter-8-disk-6" {
  name     = "vcenter-8-disk-6"
  profile  = "10iops-tier"
  zone     = "us-south-1"
  capacity = 25
}

resource "ibm_is_volume" "vcenter-8-disk-7" {
  name     = "vcenter-8-disk-7"
  profile  = "10iops-tier"
  zone     = "us-south-1"
  capacity = 1430
}

resource "ibm_is_volume" "vcenter-8-disk-8" {
  name     = "vcenter-8-disk-8"
  profile  = "10iops-tier"
  zone     = "us-south-1"
  capacity = 10
}

resource "ibm_is_volume" "vcenter-8-disk-9" {
  name     = "vcenter-8-disk-9"
  profile  = "10iops-tier"
  zone     = "us-south-1"
  capacity = 25
}

resource "ibm_is_volume" "vcenter-8-disk-10" {
  name     = "vcenter-8-disk-10"
  profile  = "10iops-tier"
  zone     = "us-south-1"
  capacity = 25
}

resource "ibm_is_volume" "vcenter-8-disk-11" {
  name     = "vcenter-8-disk-11"
  profile  = "10iops-tier"
  zone     = "us-south-1"
  capacity = 100
}

resource "ibm_is_volume" "vcenter-8-disk-12" {
  name     = "vcenter-8-disk-12"
  profile  = "10iops-tier"
  zone     = "us-south-1"
  capacity = 100
}

resource "ibm_is_volume" "vcenter-8-disk-13" {
  name     = "vcenter-8-disk-13"
  profile  = "10iops-tier"
  zone     = "us-south-1"
  capacity = 1430
}

resource "ibm_is_volume" "vcenter-8-disk-14" {
  name     = "vcenter-8-disk-14"
  profile  = "10iops-tier"
  zone     = "us-south-1"
  capacity = 25
}

resource "ibm_is_volume" "vcenter-8-disk-15" {
  name     = "vcenter-8-disk-15"
  profile  = "10iops-tier"
  zone     = "us-south-1"
  capacity = 100
}

resource "ibm_is_volume" "vcenter-8-disk-16" {
  name     = "vcenter-8-disk-16"
  profile  = "10iops-tier"
  zone     = "us-south-1"
  capacity = 1000
}

resource "ibm_is_volume" "vcenter-server-7-0-disk-1" {
  name     = "vcenter-server-7-0-disk-1"
  profile  = "10iops-tier"
  zone     = "us-south-1"
  capacity = 6
}

resource "ibm_is_volume" "vcenter-server-7-0-disk-2" {
  name     = "vcenter-server-7-0-disk-2"
  profile  = "10iops-tier"
  zone     = "us-south-1"
  capacity = 50
}

resource "ibm_is_volume" "vcenter-server-7-0-disk-3" {
  name     = "vcenter-server-7-0-disk-3"
  profile  = "10iops-tier"
  zone     = "us-south-1"
  capacity = 50
}

resource "ibm_is_volume" "vcenter-server-7-0-disk-4" {
  name     = "vcenter-server-7-0-disk-4"
  profile  = "10iops-tier"
  zone     = "us-south-1"
  capacity = 25
}

resource "ibm_is_volume" "vcenter-server-7-0-disk-5" {
  name     = "vcenter-server-7-0-disk-5"
  profile  = "10iops-tier"
  zone     = "us-south-1"
  capacity = 25
}

resource "ibm_is_volume" "vcenter-server-7-0-disk-6" {
  name     = "vcenter-server-7-0-disk-6"
  profile  = "10iops-tier"
  zone     = "us-south-1"
  capacity = 25
}

resource "ibm_is_volume" "vcenter-server-7-0-disk-7" {
  name     = "vcenter-server-7-0-disk-7"
  profile  = "10iops-tier"
  zone     = "us-south-1"
  capacity = 50
}

resource "ibm_is_volume" "vcenter-server-7-0-disk-8" {
  name     = "vcenter-server-7-0-disk-8"
  profile  = "10iops-tier"
  zone     = "us-south-1"
  capacity = 10
}

resource "ibm_is_volume" "vcenter-server-7-0-disk-9" {
  name     = "vcenter-server-7-0-disk-9"
  profile  = "10iops-tier"
  zone     = "us-south-1"
  capacity = 25
}

resource "ibm_is_volume" "vcenter-server-7-0-disk-10" {
  name     = "vcenter-server-7-0-disk-10"
  profile  = "10iops-tier"
  zone     = "us-south-1"
  capacity = 25
}

resource "ibm_is_volume" "vcenter-server-7-0-disk-11" {
  name     = "vcenter-server-7-0-disk-11"
  profile  = "10iops-tier"
  zone     = "us-south-1"
  capacity = 100
}

resource "ibm_is_volume" "vcenter-server-7-0-disk-12" {
  name     = "vcenter-server-7-0-disk-12"
  profile  = "10iops-tier"
  zone     = "us-south-1"
  capacity = 100
}

resource "ibm_is_volume" "vcenter-server-7-0-disk-13" {
  name     = "vcenter-server-7-0-disk-13"
  profile  = "10iops-tier"
  zone     = "us-south-1"
  capacity = 50
}

resource "ibm_is_volume" "vcenter-server-7-0-disk-14" {
  name     = "vcenter-server-7-0-disk-14"
  profile  = "10iops-tier"
  zone     = "us-south-1"
  capacity = 25
}

resource "ibm_is_volume" "vcenter-server-7-0-disk-15" {
  name     = "vcenter-server-7-0-disk-15"
  profile  = "10iops-tier"
  zone     = "us-south-1"
  capacity = 100
}

resource "ibm_is_volume" "vcenter-server-7-0-disk-16" {
  name     = "vcenter-server-7-0-disk-16"
  profile  = "10iops-tier"
  zone     = "us-south-1"
  capacity = 200
}

resource "ibm_is_volume" "was-dev-va-hicloud-disk-1" {
  name     = "was-dev-va-hicloud-disk-1"
  profile  = "10iops-tier"
  zone     = "us-south-1"
  capacity = 80
}

resource "ibm_is_volume" "was-prod-va-hicloud-disk-1" {
  name     = "was-prod-va-hicloud-disk-1"
  profile  = "10iops-tier"
  zone     = "us-south-1"
  capacity = 80
}

resource "ibm_is_volume" "was-sit-va-hicloud-disk-1" {
  name     = "was-sit-va-hicloud-disk-1"
  profile  = "10iops-tier"
  zone     = "us-south-1"
  capacity = 128
}

resource "ibm_is_volume" "was-stg-va-hicloud-disk-1" {
  name     = "was-stg-va-hicloud-disk-1"
  profile  = "10iops-tier"
  zone     = "us-south-1"
  capacity = 75
}

resource "ibm_is_volume" "was1-prod-va-hicloud-disk-1" {
  name     = "was1-prod-va-hicloud-disk-1"
  profile  = "10iops-tier"
  zone     = "us-south-1"
  capacity = 75
}

resource "ibm_is_volume" "was1-stg-va-hicloud-disk-1" {
  name     = "was1-stg-va-hicloud-disk-1"
  profile  = "10iops-tier"
  zone     = "us-south-1"
  capacity = 75
}

resource "ibm_is_volume" "wasnd-portal-prod-va-hicloud-disk-1" {
  name     = "wasnd-portal-prod-va-hicloud-disk-1"
  profile  = "10iops-tier"
  zone     = "us-south-1"
  capacity = 60
}

resource "ibm_is_volume" "wasnd-portal-stg-va-hicloud-disk-1" {
  name     = "wasnd-portal-stg-va-hicloud-disk-1"
  profile  = "10iops-tier"
  zone     = "us-south-1"
  capacity = 75
}

resource "ibm_is_volume" "wasnd-portal1-prod-va-hicloud-disk-1" {
  name     = "wasnd-portal1-prod-va-hicloud-disk-1"
  profile  = "10iops-tier"
  zone     = "us-south-1"
  capacity = 60
}

resource "ibm_is_volume" "wasnd-portal1-stg-va-hicloud-disk-1" {
  name     = "wasnd-portal1-stg-va-hicloud-disk-1"
  profile  = "10iops-tier"
  zone     = "us-south-1"
  capacity = 75
}

resource "ibm_is_volume" "was-portal-sit-va-hicloud-disk-1" {
  name     = "was-portal-sit-va-hicloud-disk-1"
  profile  = "10iops-tier"
  zone     = "us-south-1"
  capacity = 72
}

resource "ibm_is_volume" "was-portal-sit-va-hicloud-disk-2" {
  name     = "was-portal-sit-va-hicloud-disk-2"
  profile  = "10iops-tier"
  zone     = "us-south-1"
  capacity = 70
}

resource "ibm_is_volume" "webmaint-dmz-va-hicloud-disk-1" {
  name     = "webmaint-dmz-va-hicloud-disk-1"
  profile  = "10iops-tier"
  zone     = "us-south-1"
  capacity = 72
}

resource "ibm_is_volume" "webmaint-prod-va-hicloud-disk-1" {
  name     = "webmaint-prod-va-hicloud-disk-1"
  profile  = "10iops-tier"
  zone     = "us-south-1"
  capacity = 72
}

resource "ibm_is_volume" "winutility20-va-hicloud-disk-1" {
  name     = "winutility20-va-hicloud-disk-1"
  profile  = "10iops-tier"
  zone     = "us-south-1"
  capacity = 100
}

resource "ibm_is_volume" "wsus01-va-hicloud-disk-1" {
  name     = "wsus01-va-hicloud-disk-1"
  profile  = "10iops-tier"
  zone     = "us-south-1"
  capacity = 820
}
