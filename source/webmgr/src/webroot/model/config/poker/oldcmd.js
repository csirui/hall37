/**
 * @ author: wenshan @ date: 2015.3.24 @ from: index js
 */

$(function() {
      // 加载菜单请求
      var jsonfile = 'poker/oldcmd.json';
      var jsonvue = null;
      var convertDatas = function(datas) {
        var commands = [];
        for (var old in datas) {
          var cmds = datas[old];
          cmds['old'] = old;
          commands.push(cmds);
        }
        return {'cmds' : commands};
      };

      var savedata = function(datas) {
        var commands = {};
        datas = SS.clone(datas)['cmds'];
        for (var x in datas) {
          var cmds = datas[x];
          var old = cmds['old'];
          cmds['old'] = undefined;
          cmds['c2s'] = undefined;
          cmds['s2c'] = undefined;
          commands[old] = cmds;
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
                            'old' : '',
                            'cmd' : '',
                            'act' : '',
                            'target' : '',
                            'memory' : ''
                          });
                    }
                  }
                });
          });
    });
