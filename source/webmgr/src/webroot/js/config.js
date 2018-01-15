/**
 * Created by windaoo on 16/8/26.
 */
/**
 * @ author: wenshan @ date: 2015.3.24 @ from: index js
 * editby wangtao date: 2016.1.13
 */


var commonReqParams;
commonReqParams = {
    gameId: globalGameId,
    name: globalConfigName
};

function http_generate(callback) {
    var params = extend({
        action: "generate"
    }, commonReqParams);

    SS.getData(SS.url.model.config, params, callback);
}

function http_svnLog(branch, callback) {
    var params = extend({
        action: "svnLog",
        branch: branch
    }, commonReqParams);

    SS.getData(SS.url.model.config, params, callback);
}

function http_commit(commitLog, branch, callback) {
    var params = extend({
        action: "commit",
        log: commitLog,
        branch: branch
    }, commonReqParams);

    SS.setData(SS.url.model.config, params, callback);
}

function commit_testing() {
    var branch = 'testing';
    http_generate(function (da) {
        var htmls = [];
        if (da.result.isOk) {
            htmls.push("生成成功！<br />");
            if (da.result.modified) {
                make_commit_elems(htmls, branch, '');
            } else {
                htmls.push("不过没有新的改动<br />");
            }
            $('#center_div').html(htmls.join(""));
            $('#commit_btn').attr('data-branch', branch);
        } else {
            htmls.push("失败！<br />");
            if (da.result.error) {
                var errinfo = da.result.error.split('\n').join("<br />");
                htmls.push('<pre>');
                htmls.push(errinfo);
                htmls.push('</pre>');
                $('#center_div').html(htmls.join(""));
            }
        }
    });
}

function commit_release() {
    var branch = 'release';
    http_svnLog('testing', function (da) {
        var htmls = [];
        var svnlog = da.result.svnLog;
        make_commit_elems(htmls, branch, svnlog);
        $('#center_div').html(htmls.join(""));
        $('#commit_btn').attr('data-branch', branch);
    });
}

function filterBlanksAndComment(multiLineStr) {
    var lines = [];
    var splited = multiLineStr.split("\n");
    for (var lineno in splited) {
        var line = splited[lineno];
        if (line[0] == '#') {
            continue
        }
        var len = lines.length;
        if (line == '' && len > 0 && lines[len - 1] == '') {
            continue
        }
        lines.push(line);
    }
    return lines.join("\n");
}

function commit() {
    var log = $('#commitlog').val();
    var branch = $('#commit_btn').attr("data-branch");

    log = filterBlanksAndComment(log);
    var htmllog = log.split("\n").join("<br/>");

    $.messager.confirm(
        "提交日志和内容都检查过了吗?",
        "<h4>提交日志:</h4><br/>" + htmllog,
        function (data) {
            if (data) {
                http_commit(log, branch, function (da) {
                    var htmls = [];
                    htmls.push(da.result.output);
                    $('#center_div').html(htmls.join(""));
                });
            }
        });
}

function make_commit_elems(htmls, branch, svnlog) {
    htmls.push("<span>提交日志：</span>");
    htmls.push("<br />");
    htmls.push('<textarea id="commitlog" style="width:1000px;height:200px;">' +
        '{0}</textarea>'.format(svnlog));
    htmls.push('<button id="commit_btn" onclick="commit()">提交</button>');

    var diffhtml = "";
    if (branch == 'testing') {
         diffhtml = getDiffIframeHtml(
            'testing', 'LOCAL', '已修改版本',
            'testing', 'HEAD', 'testing上次提交的版本'
        );
    } else if (branch == 'release') {
        diffhtml = getDiffIframeHtml(
            'testing', 'HEAD', 'testing版本',
            'release', 'HEAD', 'release版本'
        );
    } else if (branch == 'online') {
        diffhtml = getDiffIframeHtml(
            'release', 'HEAD', 'release版本',
            'online', 'HEAD', 'online版本'
        );
    }
    htmls.push(diffhtml);

}

function getDiffIframeHtml(newBranch, newVer, newName, oldBranch, oldVer, oldName) {
    var commonPart = [
        "action=get",
        "gameId=" + globalGameId,
        "name=" + globalConfigName
    ];
    var newParams = commonPart.concat([
        "branch=" + newBranch,
        "revision=" + newVer,
        "diffName=" + '/' + newName + '.json'
    ]);
    var oldParams = commonPart.concat([
        "branch=" + oldBranch,
        "revision=" + oldVer,
        "diffName=" + '/' + oldName + '.json'
    ]);

    var new_ = SS.host + '/config?' + encodeURIComponent(newParams.join("&"));
    var old_ = SS.host + '/config?' + encodeURIComponent(oldParams.join("&"));

    var src = '/js/jsondiff/diff.html?' +
        'desc=http raw file urls' +
        '&left=' + old_ +
        '&right=' + new_;

    return '<iframe name="diff_iframe"'
        + ' frameborder="0"'
        + ' style="width:100%;height:100%;"'
        + ' src="' + src + '"'
        + '>'
        + '</iframe>';
}