job "countdash" {
  datacenters = ["dc1"]

  # Start API group
  group "api" {
    network {
      mode = "bridge"
    }

    service {
      name = "count-api"
      port = "9001"

      connect {
        sidecar_service {}
      }
    }

    task "web" {
      driver = "docker"
      config {
        image = "hashicorpnomad/counter-api:v1"
      }
    } # End task
  } # End group

  # Start Dashboard Group
  group "dashboard" {
    network {
      mode = "bridge"
      port "http" {
        static = 9002
        to     = 9002
      }
    }

    service {
      # Registers its service with consul under
      # 'count-dashboard' at port 9002
      name = "count-dashboard"
      port = "9002"
      tags = ["urlprefix-/"]

      connect {
        sidecar_service {
          proxy {

            # This service feeds from others, such as 'count-api'
            # The local envoy port for that information is port 8080
            upstreams {
              destination_name = "count-api"
              local_bind_port = 8080
            }
          }
        }
      }
    }

    task "dashboard" {
      driver = "docker"

      # The environment variables help set up the dashboard
      env {
        COUNTING_SERVICE_URL = "http://${NOMAD_UPSTREAM_ADDR_count_api}"
      }
      
      config {
        image = "hashicorpnomad/counter-dashboard:v1"
      }
    } # End task
  } # End group

 } # End job