job "apidb" {
	datacenters = ["dc1"]

  # Start mongo group
  group "mongo" {
    count = 1

    network {
      mode = "bridge"
      # For service check we want 
      # to expose the port. Ideally
      # we find a smaller surface area 
      # to expose, for now we let it touch 
      # all of it.
      port "mongo" {
        to = 27017
      }
    }

    service {
      name = "mongodb"
      port = 27017
      tags = ["database"]

      connect {
        sidecar_service {
          tags = ["proxy"]
          proxy {
            local_service_address = "${attr.unique.network.ip-address}"
          }
        }
      }

      check {
        type = "http"
        name = "mongodb-health"
        port = "mongo"
        path = "/"
        expose = true
        interval = "30s"
        timeout  = "5s"
      }
    }

    task "mongo" {
      driver = "docker"

      config {
        image = "mongo"
        port_map {
          mongo = 27017
        }
      }

      resources {
        cpu    = 500 # MHz
        memory = 128 # MB

        network {
          mbits = 100
        }
      }
    } # End task

  } # End group

  # Start api group
  group "api" {
    count = 3
		network {
			mode = "bridge"
			port "http" {
				to = 5000
			}
		}

		service {
			name = "api-frontend"
			port = "http"
			tags = ["urlprefix-/"]

			check {
        type = "http"
        path = "/"
        interval = "30s"
        timeout  = "5s"
      }
			
      connect {
				sidecar_service{
					tags = ["proxy"]
					proxy {
            local_service_address = "${attr.unique.network.ip-address}"
						upstreams {
							destination_name = "mongodb"
							local_bind_port = 27017
						}
					}
				}
			}
		}

		task "api" {
      driver = "docker"

      env {
        MONGO_IP = "${NOMAD_UPSTREAM_ADDR_mongodb}"
      }

      config {
        image = "bluchterhand/cloudarchitects-api:0.4"
        port_map {
          http = 5000
        }
      }

      resources {
        cpu = 500 # 500 MHz
        memory = 128 # 128MB
        network {
          mbits = 100
        }
      }
		} # End task
	} # End group

} # End job
