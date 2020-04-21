job "geojson" {
	datacenters = ["dc1"]
  type = "service"

  group "geojson" {
    count = 1

		task "geojson" {
      driver = "docker"

      config {
        image = "xaviermerino/covid-geojson:latest"

        port_map {
          http = 1270
        }
      }

      resources {
        cpu = 1000 
        memory = 500 
        network {
          mbits = 100
          mode = "host"
        }
      }

      service {
        name = "geojson"
        port = "http"
        check {
          name     = "GeoJSON Health Check"
          type     = "http"
          path     = "/"
          interval = "5s"
          timeout  = "2s"
        }
      }

		} # End task

	} # End group

} # End job
