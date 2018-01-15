/**
 * @ author: wenshan @ date: 2015.3.24 @ from: index js
 */

$(function() {
  // 加载菜单请求
  var jsonfile = 'freetime/server.json';
  var jsonvue = null;
  var mindex = 1;
  var convertInnerList = function(data) {
    if (typeof(data) == 'object') {
      return data.join(',');
    }
    return data;
  };
  var convertInnerListBack = function(data) {
    if (data) {
      if (typeof(data) == 'object') {
        return data;
      }
      if (data.indexOf('${{') == 0) {
        return data;
      }
      var dlist = [];
      data = data.split(',');
      for (var x = 0; x < data.length; x++) {
        var d = $.trim(data[x]);
        if (d.length > 0) {
          dlist.push(d);
        }
      }
      return dlist;
    }
    return data;
  };
  var convertInnerPortBack = function(data) {
    if (data) {
      if (data.indexOf('${{') == 0) {
        return data;
      }
      return parseInt(data);
    }
    return data;
  };
  var sortConst = {
    'PL' : 1,
    'HT' : 2,
    'BI' : 3,
    'AG' : 4,
    'CO' : 5,
    'RB' : 6,
    'CT' : 7,
    'UT' : 8,
    'GR' : 9,
    'GT' : 10
  };
  var convertDatas = function(datas) {
    var servers = {
      'PL' : [],
      'HT' : [],
      'BI' : [],
      'AG' : [],
      'CO' : [],
      'RB' : [],
      'UT' : [],
      'CT' : [],
      'GR' : [],
      'GT' : []
    };
    for (var x in datas) {
      var srv = datas[x];
      var stype = srv['type'];
      var sdata = {};
      var redis = convertInnerList(srv['redis']);
      var mysql = convertInnerList(srv['mysql']);
      if (stype == 'PL' || stype == 'HT' || stype == 'BI') {
        sdata = {
          id : srv['id'],
          ip : srv['ip'],
          agent : srv['agent'],
          ht_http : '' + srv['protocols']['server']['ht-http'],
          redis : redis,
          mysql : mysql
        };
      }
      if (stype == 'AG') {
        sdata = {
          id : srv['id'],
          ip : srv['ip'],
          a2a : '' + srv['protocols']['server']['a2a'],
          a2s : '' + srv['protocols']['server']['a2s']
        };
      }
      if (stype == 'CO') {
        sdata = {
          id : srv['id'],
          ip : srv['ip'],
          agent : srv['agent'],
          co_tcp : '' + srv['protocols']['server']['co-tcp'],
          redis : redis,
          mysql : mysql
        };
      }
      if (stype == 'RB' || stype == 'GR' || stype == 'GT' || stype == 'UT' || stype == 'CT') {
        sdata = {
          id : srv['id'],
          ip : srv['ip'],
          agent : srv['agent'],
          redis : redis,
          mysql : mysql
        };
      }
      servers[stype].push(sdata);
    }
    return servers;
  };

  var savedata = function(datas) {
    var servers = [];
    datas = SS.clone(datas);
    for (var stype in datas) {
      var srvs = datas[stype];
      for (var x in srvs) {
        var srv = srvs[x];
        var sdata = null;
        if (stype == 'PL' || stype == 'HT' || stype == 'BI') {
          sdata = {
            id : srv['id'],
            ip : srv['ip'],
            agent : srv['agent'],
            protocols : {
              server : {
                'ht-http' : srv['ht_http']
              }
            },
            redis : convertInnerListBack(srv['redis']),
            mysql : convertInnerListBack(srv['mysql'])
          };
        }
        if (stype == 'AG') {
          sdata = {
            id : srv['id'],
            ip : srv['ip'],
            protocols : {
              server : {
                'a2a' : srv['a2a'],
                'a2s' : srv['a2s']
              }
            }
          };
        }
        if (stype == 'CO') {
          sdata = {
            id : srv['id'],
            ip : srv['ip'],
            agent : srv['agent'],
            protocols : {
              server : {
                'co-tcp' : srv['co_tcp']
              }
            },
            redis : convertInnerListBack(srv['redis']),
            mysql : convertInnerListBack(srv['mysql'])
          };
        }
        if (stype == 'RB' || stype == 'GR' || stype == 'GT' || stype == 'UT' || stype == 'CT') {
          sdata = {
            id : srv['id'],
            ip : srv['ip'],
            agent : srv['agent'],
            redis : convertInnerListBack(srv['redis']),
            mysql : convertInnerListBack(srv['mysql'])
          };
        }
        sdata['type'] = stype;
        servers.push(sdata);
      }
    }
    servers.sort(function(a, b) {
          var t1 = sortConst[a['type']];
          var t2 = sortConst[b['type']];
          if (t1 == t2) {
            var id1 = a['id'];
            var id2 = b['id'];
            return id1 > id2 ? 1 : -1;
          }
          return t1 > t2 ? 1 : -1;
        });
    var params = {
      jsonfile : jsonfile,
      jsondata : JSON.stringify(servers)
    }
    SS.setData(SS.url.model.set_json_file, params, function(da) {
          if (da.error) {
            alert('ERROR !! ' + JSON.stringify(da.error));
          } else {
            alert('SAVE DATA OK');
          }
          $('.btn-success').show();
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
          $('.btn-success').hide();
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
          var sdata = null;
          if (stype == 'PL' || stype == 'HT' || stype == 'BI') {
            sdata = {
              id : mid,
              ip : '',
              agent : '',
              pl_http : '0',
              redis : '',
              mysql : ''
            };
          }
          if (stype == 'AG') {
            sdata = {
              id : mid,
              ip : '',
              a2a : '0',
              a2s : '0'
            };
          }
          if (stype == 'CO') {
            sdata = {
              id : mid,
              ip : '',
              agent : '',
              co_tcp : '0',
              redis : '',
              mysql : ''
            };
          }
          if (stype == 'RB' || stype == 'GR' || stype == 'GT' || stype == 'UT' || stype == 'CT') {
            sdata = {
              id : mid,
              ip : '',
              agent : '',
              redis : '',
              mysql : ''
            };
          }
          mslist.unshift(sdata);
        }
      }
    });
  });
});
