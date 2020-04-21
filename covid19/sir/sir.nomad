job "sir" {
	datacenters = ["dc1"]
  type = "service"

  group "sir" {
    count = 1

		task "sir" {
      driver = "docker"

      config {
        image = "xaviermerino/covid-sir:latest"

        port_map {
          http = 5000
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
        name = "sir"
        port = "http"
        check {
          name     = "SIR Model Health Check"
          type     = "http"
          path     = "/"
          interval = "5s"
          timeout  = "2s"
        }
      }

		} # End task

	} # End group

} # End job
