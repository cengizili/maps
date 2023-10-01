provider "google" {
  project = "speedy-post-400711"
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
      container_concurrency = 1
      containers {
        image = "gcr.io/speedy-post-400711/app"
        resources {
            limits = {
                cpu = "2000m" # 1 vCPU
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
