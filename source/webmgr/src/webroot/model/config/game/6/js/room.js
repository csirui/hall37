
function RoomListener() {
}

RoomListener.prototype.updateRooms = function(rm) {
	roomListElt = document.getElementById('roomlist');
	removeAllChild(roomListElt);
	ol = document.createElement('ol');
	for (var roomId in rm.roomMap) {
		console.log('updateRooms add roomId=', roomId, typeof(roomId));
		room = rm.roomMap[roomId];
		li = document.createElement('li');
		span = document.createElement('span');
		span.setAttribute('class', 'roomListItem');
		span.innerHTML = room.name + '(' + roomId + ')';
		li.appendChild(span);
		ol.appendChild(li);
	}
	roomListElt.appendChild(ol);
}

RoomListener.prototype.onStateChanged = function(rm) {
	switch(rm.state) {
		case 1:
			console.log('RoomManager loading...');
			break;
		case 2:
			console.log('RoomManager loaded');
			this.updateRooms(rm);
			break;
	}
}

RoomListener.prototype.onSelectedChanged = function(rm) {
	console.log('RoomListener.onSelectedChanged roomId=', rm.getSelectedRoomId());
	room = rm.getSelectedRoom();
	if (!!room) {
		roomModel = RoomModel.decode(parseInt(rm._selectedRoomId), rm.getSelectedRoom());
		eltId = 'roomedit-' + roomModel.typeName;
		roomedit = document.getElementById(eltId);
		console.log('RoomListener.onSelectedChanged roomId=', rm.getSelectedRoomId(),
					'roomeditId=', eltId,
					'roomedit=', roomedit);
		RoomModelView.createView(roomedit, roomModel);
	}
}

function RoomManager(listener) {
	// key=roomId, value=roomConf
	this.roomMap = {};
	// 监听器
	this.listener = listener;
	// 0; 1 正在加载中; 2 加载完成；
	this.state = 0;
	// 当前选择的房间ID
	this._selectedRoomId = null;
}

RoomManager.prototype.newRoom = function() {
	
}

RoomManager.prototype.setSelectedRoom = function(roomId) {
	if (roomId != this._selectedRoomId && !!this.roomMap[roomId]) {
		this._selectedRoomId = roomId;
		this.listener.onSelectedChanged(this);
	}
}

RoomManager.prototype.getSelectedRoom = function() {
	return this.roomMap[this._selectedRoomId] || null;
}

RoomManager.prototype.getSelectedRoomId = function() {
	return this._selectedRoomId;
}

RoomManager.prototype.load = function() {
	self = this;
	if (self.state === 0) {
		self.state = 1;
		self.listener.onStateChanged(self);
		SS.getData(SS.url.model.dizhu_room_list, {}, function(result) {
			if (result.ec != 0) {
				console.log('RoomManager.load SS.getData ec=', result.ec,
							'info=', result.info);
			} else {
				console.log('RoomManager.load SS.getData rooms=', result.rooms);
				try {
					for (var roomId in result.rooms) {
						self.roomMap[roomId] = result.rooms[roomId];
					}
					self.state = 2;
					console.log('RoomManager.load ok rooms=', result.rooms);
					self.listener.onStateChanged(self);
				} catch (e) {
					console.log('RoomManager.load SS.getData', e);
					self.state = 0;
				}
			}
		});
	}
}

DDZ.roomManager = new RoomManager(new RoomListener());

function onLoad() {
	console.log('onLoad');
	DDZ.roomManager.load();
	$("span.roomListItem").live('click', function() {
		console.log('click roomListItem', this);
	});
}

