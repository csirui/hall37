/**
 * @ author: wenshan @ date: 2015.3.24 @ from: index js
 */

$(function() {
      // 加载菜单请求
      var jsonfile = 'poker/global.json';
      var jsonvue = null;

      var savedata = function(data) {
        var params = {
          jsonfile : jsonfile,
          jsondata : JSON.stringify(data)
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
            var datas = da.result.datas;
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
