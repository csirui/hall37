/**
 * @ author: wenshan @ date: 2015.3.24 @ from: index js
 */

$(function() {
      // 加载菜单请求
      var jsonfile = 'poker/machine.json';
      var jsonvue = null;
      var mindex = 1;

      var convertDatas = function(mdata) {
        var mlist = [];
        for (var mkey in mdata) {
          var minfo = mdata[mkey];
          minfo['id'] = mkey;
          mlist.push(minfo);
        }
        var datas = {
          'machines' : mlist
        };
        return datas;
      };

      var savedata = function(data) {
        var mdatas = {}
        var mlist = SS.clone(data['machines']);
        for (var i in mlist) {
          var mi = mlist[i];
          mdatas[mi['id']] = mi;
          mi['id'] = undefined;
        }
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
                      var mslist = this.$data['machines'];
                      mslist.splice(itemkey, 1);
                    },

                    addData : function() {
                      var mslist = this.$data['machines'];
                      var mids = {};
                      for (var x in mslist) {
                        mids[mslist[x]['id']] = 1;
                      }
                      var mid = '';
                      while (true) {
                        mid = 'm' + mindex;
                        if (!(mid in mids)) {
                          break;
                        }
                        mindex++;
                      }
                      mslist.unshift({
                            "internet" : "",
                            "intranet" : "",
                            "pwd" : "",
                            "ssh" : 22,
                            "user" : "",
                            "id" : mid
                          });
                    }
                  }
                });
          });
    });
