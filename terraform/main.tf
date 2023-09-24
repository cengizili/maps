provider "google" {
  project = "instagenie-7cc10"
}


resource "google_cloud_run_service" "default" {
  count    = 100
  name     = "serp-${count.index}"
  location = "us-central1"

  metadata {
    annotations = {
      "run.googleapis.com/client-name" = "terraform"
    }
  }

  template {
    spec {
      containers {
        image = "gcr.io/instagenie-7cc10/mapss"
        resources {
            limits = {
                cpu = "1000m" # 1 vCPU
                memory = "2Gi"
            }
        }
      }
    }
  }
}

data "google_iam_policy" "noauth" {
  binding {
    role    = "roles/run.invoker"
    members = ["allUsers"]
  }
}

locals {
  cloud_run_service_map = { for service in google_cloud_run_service.default : service.name => service }
}

resource "google_cloud_run_service_iam_policy" "noauth" {
  for_each    = local.cloud_run_service_map
  location    = each.value.location
  project     = each.value.project
  service     = each.value.name

  policy_data = data.google_iam_policy.noauth.policy_data
}
