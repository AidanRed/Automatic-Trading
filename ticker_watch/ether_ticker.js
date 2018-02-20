var socket = require('socket.io-client')('https://socket.btcmarkets.net', {secure: true, transports: ['websocket'], upgrade: false});
var instrument = 'ETH';
var currency = 'AUD';
var eventName = 'newTicker';
var channelName = 'Ticker-BTCMarkets-' + instrument + "-" + currency;

socket.on('connect', function(){
	console.log('<connected>');
	socket.emit('join', channelName);
});

socket.on(eventName, function(data){
    console.log(data);
});

socket.on('disconnect', function(){
	console.log('<disconnected>');
});
