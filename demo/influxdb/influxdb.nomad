job "influxdb" {
  datacenters = ["dc1"]

  # Start api group
  group "covid-db" {
    count = 1

    // volume "influxdb" {
    //   type      = "host"
    //   read_only = false
    //   source    = "influxdb"
    // }

		task "covid-db" {
      driver = "docker"

      // volume_mount {
      //   volume      = "influxdb"
      //   destination = "/var/lib/influxdb"
      //   read_only   = false
      // }

      artifact {
        source      = "https://raw.githubusercontent.com/xaviermerino/nomad-jobs/master/demo/influxdb/influxdb.conf"
        destination = "/local/"
      }

      artifact {
        source      = "https://raw.githubusercontent.com/xaviermerino/nomad-jobs/master/demo/influxdb/influxdb-init.iql"
        destination = "/local/"
      }

      config {
        image = "influxdb"
        args = [
          "-config", "/etc/influxdb/influxdb.conf"
        ]
        
        port_map {
          http = 8086
        }

        volumes = [
          "local/influxdb.conf:/etc/influxdb/influxdb.conf",
          "local/influxdb-init.iql:/docker-entrypoint-initdb.d/influxdb-init.iql"
        ]
      }

      resources {
        cpu = 500 
        memory = 300 
        network {
          mbits = 100
          port "http" {
            static = 8086
          }
        }
      }

		} # End task

	} # End group

} # End job
