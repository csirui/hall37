/**
 * @ author: wenshan @ date: 2015.3.24 @ from: index js
 */

$(function() {
      // 加载菜单请求
      var jsonfile = 'freetime/db.json';
      var jsonvue = null;
      var mindex = 1;
      var dbschema = {
        "redis" : ["mix", "keymap", "dizhu", "rank", "geo", "friend", "paydata",
            "online", "user0", "user1", "user2", "user3", "user4", "user5",
            "user6", "user7", "table0", "table1", "table2", "table3"],
        "mysql" : ["user0", "user1", "user2", "user3", "user4", "user5",
            "user6", "user7"]
      };
      var convertDatas = function(mdata) {
        var redis = {};
        var mysql = {};
        var redisval = mdata['redis'] ? mdata['redis'] : {};
        for (var x in dbschema['redis']) {
          var k = dbschema['redis'][x];
          var vlist = redisval[k];
          redis[k] = {
            ip : vlist[0],
            port : vlist[1],
            dbid : vlist[2],
            count : vlist[3]
          };
        }
        var mysqlval = mdata['mysql'] ? mdata['mysql'] : {};
        for (var x in dbschema['mysql']) {
          var k = dbschema['mysql'][x];
          var vlist = mysqlval[k];
          mysql[k] = {
            ip : vlist[0],
            port : vlist[1],
            schema : vlist[2],
            user : vlist[3],
            pwd : vlist[4]
          };
        }
        return {
          mysql : mysql,
          redis : redis
        };
      };

      var savedata = function(data) {
        var redis = {};
        var mysql = {};
        var redisval = data['redis'];
        for (var x in dbschema['redis']) {
          var k = dbschema['redis'][x];
          var vdict = redisval[k];
          redis[k] = [vdict['ip'], vdict['port'], vdict['dbid'], vdict['count']];
        }
        var mysqlval = data['mysql'];
        for (var x in dbschema['mysql']) {
          var k = dbschema['mysql'][x];
          var vdict = mysqlval[k];
          mysql[k] = [vdict['ip'], vdict['port'], vdict['schema'],
              vdict['user'], vdict['pwd']];
        }

        var params = {
          jsonfile : jsonfile,
          jsondata : JSON.stringify({
                redis : redis,
                mysql : mysql
              })
        }
        SS.setData(SS.url.model.set_json_file, params, function(da) {
              if (da.error) {
                alert('ERROR !! ' + JSON.stringify(da.error));
              } else {
                alert('SAVE DATA OK');
              }
            });
      };

      var params = {
        jsonfile : jsonfile
      };
      SS.getData(SS.url.model.get_json_file, params, function(da) {
            // 加载数据
            var datas = convertDatas(da.result.datas);
            jsonvue = new Vue({
                  el : '#dataContent',
                  data : datas,
                  methods : {

                    submit : function() {
                      savedata(this.$data);
                    },

                    reset : function() {
                      reloadPage();
                    }
                  }
                });
          });
    });
