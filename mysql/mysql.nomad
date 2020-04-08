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
        MYSQL_DATABASE = "covid19"
      }

      artifact {
        source      = "https://raw.githubusercontent.com/pcm-dpc/COVID-19/master/dati-province/dpc-covid19-ita-province.csv"
        destination = "/var/lib/mysql-files/dpc-covid19-ita-province.csv"
      }

      artifact {
        source      = "https://raw.githubusercontent.com/xaviermerino/nomad-jobs/master/mysql/ingest.sql"
        destination = "/docker-entrypoint-initdb.d/"
      }

      artifact {
        source      = "https://raw.githubusercontent.com/xaviermerino/nomad-jobs/master/mysql/ingest.sql"
        destination = "/local/"
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
