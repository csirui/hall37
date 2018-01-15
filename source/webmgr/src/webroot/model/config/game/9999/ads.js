/**
 * @ author: wenshan @ date: 2015.3.24 @ from: index js
 */

$(function() {
      // 加载菜单请求
      var jsonfile = 'game/9999/ads/0.json';
      var jsonvue = null;
      var mindex = 1;

      var convertDatas = function(mdata) {
        // alert('convertDatas: ' + JSON.stringify(mdata));
        var mlist = mdata['ads'];
        var mtms = [];
        var tms = mdata['templates']
        for (tm in tms) {
          var mtm = {};
          mtm['name'] = tm;
          mtm['interval'] = tms[tm]['interval'];
          mtm['ads'] = JSON.stringify(tms[tm]['ads']);
          mtms.push(mtm);
        };

        // alert('convertDatas 1 : ' + JSON.stringify(mlist));
        // alert('convertDatas 2 : ' + JSON.stringify(mtms));
        var datas = {
          'ads' : mlist,
          'templates': mtms
        };
        return datas;
      };

      var savedata = function(data) {
        // alert('savedata 1 : ' + JSON.stringify(data));
        var mdatas = {}
        mdatas['ads'] = [];
        mdatas['templates'] = {};

        // 保存mlist
        var mlist = SS.clone(data['ads']);
        mdatas['ads'] = mlist;
        // alert('savedata 2 : ' + JSON.stringify(mdatas));

        // 保存templates
        var mts = SS.clone(data['templates']);
        // alert('savedata 2 : ' + JSON.stringify(mts));

        for (var i in mts) {
          // alert('savedata templates: ' + JSON.stringify(i));
          var tm = mts[i];
          var newt = {};
          newt['name'] = tm['name'];
          newt['interval'] = tm['interval'];
          newt['ads'] = JSON.parse(tm['ads']);
          // alert(JSON.stringify(newt));
          mdatas['templates'][newt['name']] = newt;
          // alert(mdatas['templates']);
        };

        // alert('savedata 3 : ' + JSON.stringify(mdatas));	

        var params = {
          jsonfile : jsonfile,
          jsondata : JSON.stringify(mdatas)
        };

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
                      var mslist = this.$data['ads'];
                      mslist.splice(itemkey, 1);
                    },

                    removeTMData: function(itemkey) {
                      // alert('removeTMData...');
                      var tmlist = this.$data['templates'];
                      tmlist.splice(itemkey, 1);
                    },

                    addData : function() {
                      var mslist = this.$data['ads'];
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
                            "pic" : "",
                            "clickable" : "1",
                            "startTime" : "",
                            "endTime": ""
                          });
                    },

                    addTMData: function(){
                      // alert('addTMData...');
                      var tmlist = this.$data['templates'];
                      tmlist.unshift({
                        "name": "",
                        "interval": "5",
                        "ads": ""
                      });
                    }
                  }
                });
          });
    });
