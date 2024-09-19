const { v4: uuidv4} = require('uuid');

async function setClientId(context, events) {
    context.headers.ClientId = uuidv4();
    // console.log(context)
}

module.exports = {
    setClientId: setClientId
}