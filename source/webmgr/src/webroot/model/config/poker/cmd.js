/**
 * @ author: wenshan @ date: 2015.3.24 @ from: index js
 */

$(function() {
      // 加载菜单请求
      var jsonfile = 'poker/cmd.json';
      var jsonvue = null;
      var convertDatas = function(datas) {
        var commands = {
          'UT' : [],
          'GR' : [],
          'GT' : []
        };
        for (var stype in datas) {
          var cmds = datas[stype];
          var vlist = commands[stype];
          for (var x in cmds) {
            var cmd = cmds[x];
            cmd['cmd'] = x;
            vlist.push(cmd);
          }
          vlist.sort();
        }
        return commands;
      };

      var savedata = function(datas) {
        var commands = {
          'UT' : {},
          'GR' : {},
          'GT' : {}
        };
        datas = SS.clone(datas);
        for (var stype in datas) {
          var cmds = datas[stype];
          var vdict = commands[stype];
          for (var x in cmds) {
            var cmd = cmds[x];
            vdict[cmd['cmd']] = cmd;
            cmd['cmd'] = undefined;
          }
        }
        var params = {
          jsonfile : jsonfile,
          jsondata : JSON.stringify(commands)
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
                    },

                    removeData : function(stype, itemkey) {
                      var mslist = this.$data[stype];
                      mslist.splice(itemkey, 1);
                    },

                    addData : function(stype) {
                      var mslist = this.$data[stype];
                      mslist.unshift({
                            'cmd' : '',
                            'desc' : ''
                          });
                    }
                  }
                });
          });
    });
