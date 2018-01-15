/**
 * @ author: wenshan @ date: 2015.3.24 @ from: index js
 */

$(function() {
      // 加载菜单请求
      var jsonfile = 'game/9999/menulist/0.json';
      var jsonvue = null;
      var mindex = 1;

      var convertDatas = function(mdata) {
        var mlist = [];
        for (var mkey in mdata['templates']) {
          // alert('template: ' + JSON.stringify(mkey));
          // alert('content: ' + JSON.stringify(mdata['templates'][mkey]));

          var minfo = {};
          minfo['template'] = mkey;
          minfo['content'] = JSON.stringify(mdata['templates'][mkey]);
          mlist.push(minfo);
        }

        // alert('convertDatas: ' + JSON.stringify(mlist));
        var datas = {
          'menulists' : mlist
        };
        return datas;
      };

      var savedata = function(data) {
        // alert('savedata: ' + JSON.stringify(data));
        var mdatas = {};
        mdatas['templates'] = {};

        var mlist = SS.clone(data['menulists']);
        for (var i in mlist) {
          var key = mlist[i]['template'];
          var value = mlist[i]['content'];
          mdatas['templates'][key] = JSON.parse(value);
        }
	// alert('savedata: ' + JSON.stringify(mdatas));	

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

      // 读取文件
      var params = {
        jsonfile : jsonfile
      };

      SS.getData(SS.url.model.get_json_file, params, function(da) {
            // 加载数据
            // alert('getData: ' + JSON.stringify(da.result.datas));
            var datas = convertDatas(da.result.datas);
            // alert(datas);
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
                      var mslist = this.$data['menulists'];
                      mslist.splice(itemkey, 1);
                    },

                    addData : function() {
                      var mslist = this.$data['menulists'];
                      var mids = {};
                      for (var x in mslist) {
                        mids['id' + parseInt(mslist[x]['id'])] = 1;
                      }
                      var mid = '';
                      while (true) {
                        mid = '' + mindex;
                        if (!('id' + mid in mids)) {
                          break;
                        }
                        mindex++;
                      }
                      mslist.unshift({
                            "id" : mid,
                            "template" : "default",
                            "content" : ""
                          });
                    }
                  }
                });
          });
    });
