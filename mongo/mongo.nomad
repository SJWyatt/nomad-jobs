job "mongodb" {
	datacenters = ["dc1"]
  	type = "service"

	group "mongo" {
		count = 1
		task "mongo" {
			driver = "docker"

			config {
				image = "mongo"
				port_map {
					db = 27017	# MongoDB port
				}
			}

			resources {
				cpu    = 500 # MHz
				memory = 256 # MB

				network {
					mbits = 100
					port "db" {}
				}
			}

			service {
				name = "mongodb"
				port = "db"
				
				check {
					type = "tcp"
					interval = "10s"
					timeout = "2s"
				}				
			}
		}
	}
}
