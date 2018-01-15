/**
 * @ author: wenshan @ date: 2015.3.24 @ from: index js
 */

$(function() {
      // 加载菜单请求
      var jsonfile = 'poker/project.json';
      var jsonvue = null;
      var mindex = 1;

      var convertDatas = function(mdata) {
        return {
          'project' : mdata
        };
      };

      var savedata = function(data) {
        var mdatas = SS.clone(data['project']);
        mdatas.sort(function(a, b) {
              var p1 = a['index'];
              var p2 = b['index'];
              return p1 > p2 ? 1 : -1;
            });
        var params = {
          jsonfile : jsonfile,
          jsondata : JSON.stringify(mdatas)
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

                    removeData : function(itemkey) {
                      var mslist = this.$data['project'];
                      mslist.splice(itemkey, 1);
                    },

                    addData : function() {
                      var mslist = this.$data['project'];
                      mslist.unshift({
                            "path" : "",
                            "index" : 0,
                            "gameId" : 0
                          });
                    }
                  }
                });
          });
    });
