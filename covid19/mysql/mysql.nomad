job "mysql" {
  datacenters = ["dc1"]
  type = "service"

  group "mysql" {
    task "mysql" {
      driver = "docker"
      config {
        image = "mysql"
      }

      env {
        MYSQL_ROOT_PASSWORD = "iamgroot"
        MYSQL_DATABASE = "geolocations"
      }

      artifact {
        source      = "https://raw.githubusercontent.com/xaviermerino/nomad-jobs/master/covid19/mysql/data/af_bases.csv"
        destination = "/local/data/af_bases.csv"
      }

      artifact {
        source      = "https://raw.githubusercontent.com/xaviermerino/nomad-jobs/master/covid19/mysql/conf/ingest.sql"
        destination = "/docker-entrypoint-initdb.d/"
      }

      resources {
        cpu    = 2400
        memory = 500
        network {
          mbits = 10
          mode = "host"
          port "http" {}
        }
      }

    }
  }
}
